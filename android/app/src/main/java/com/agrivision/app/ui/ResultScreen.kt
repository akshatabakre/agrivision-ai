package com.agrivision.app.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.agrivision.app.AppViewModel
import com.agrivision.app.data.DiagnosisResult

@Composable
fun ResultScreen(vm: AppViewModel, r: DiagnosisResult) {
    val context = LocalContext.current
    val sevColour = severityColour(r.severity)
    val verdictColour = if (r.isOk) sevColour else severityColour("Unknown")

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = { vm.result = null }) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
            }
            KickerText("02 · Diagnosis" + (r.id?.let { "  #$it" } ?: ""))
        }

        if (!r.isOk && r.messages.isNotEmpty()) {
            PaperCard(Modifier.padding(bottom = 12.dp)) {
                Text(r.messages.first(), color = Color(0xFFB0651A), fontWeight = FontWeight.SemiBold)
                r.messages.drop(1).forEach { Text("- $it", fontSize = 13.sp, color = Muted) }
            }
        }

        // Verdict card
        PaperCard {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Chip(r.categoryLabel, verdictColour)
                Spacer(Modifier.size(8.dp))
                KickerText("Crop: ${r.crop}")
            }
            Text(
                r.displayName,
                style = SerifTitle.copy(fontSize = 30.sp, color = verdictColour, lineHeight = 34.sp),
                modifier = Modifier.padding(vertical = 6.dp),
            )
            Text((if (r.isOk) "Probable cause: " else "") + r.cause, fontSize = 15.sp)
            Row(Modifier.padding(top = 12.dp), horizontalArrangement = Arrangement.spacedBy(32.dp)) {
                Column {
                    KickerText("Confidence")
                    Text(
                        "%.0f%%".format(r.confidence * 100),
                        style = SerifTitle.copy(fontSize = 28.sp, color = confidenceColour(r.confidence)),
                    )
                }
                Column {
                    KickerText("Severity")
                    Text(r.severity, style = SerifTitle.copy(fontSize = 28.sp, color = sevColour))
                }
            }
        }
        Spacer(Modifier.height(10.dp))

        // Crop status card
        DarkCard {
            KickerText("Crop status", colour = Color(0xFFA39482))
            Text(RiskText[r.severity] ?: r.severity, style = SerifTitle.copy(fontSize = 28.sp, color = sevColour))
            Text(
                "HEALTH SCORE  " + (r.healthScore?.let { "$it / 100" } ?: "-- / 100"),
                color = Color(0xFFEFE6D8), fontFamily = FontFamily.Monospace, fontSize = 14.sp,
                modifier = Modifier.padding(vertical = 6.dp),
            )
            HealthBar(r.healthScore, sevColour)
            Text(
                "An AI diagnosis is an initial screening tool, not a definitive agricultural verdict.",
                color = Color(0xFFA39482), fontSize = 12.sp, modifier = Modifier.padding(top = 10.dp),
            )
        }

        if (r.isOk) {
            val rec = r.recommendation
            Section("Recommended actions · ${rec.urgency}", sevColour)
            rec.actions.forEachIndexed { i, a -> Bullet(a, "%02d".format(i + 1), Leaf) }
            rec.notes.forEach { Note(it) }

            Section("Observed symptoms")
            if (r.symptoms.isEmpty()) Bullet("No visible abnormality") else r.symptoms.forEach { Bullet(it) }

            if (rec.prevention.isNotEmpty()) {
                Section("Prevent it happening again")
                rec.prevention.forEach { Bullet(it) }
            }
        }

        // How the AI saw it
        Section("How the AI reached this result")
        val original = r.images["original"]
        val overlay = r.images["overlay"]
        if (original != null && overlay != null) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(original to "Input", overlay to "Damage map").forEach { (bmp, caption) ->
                    Column(Modifier.weight(1f)) {
                        Image(
                            bmp.asImageBitmap(), caption,
                            Modifier
                                .fillMaxWidth()
                                .aspectRatio(1f)
                                .clip(RoundedCornerShape(4.dp)),
                            contentScale = ContentScale.Crop,
                        )
                        Text(caption, fontSize = 12.sp, color = Muted)
                    }
                }
            }
            Text(
                "Green outline: leaf detected. Red: necrotic tissue. Yellow: chlorosis. Blue: powdery growth.",
                fontSize = 12.sp, color = Muted, modifier = Modifier.padding(top = 4.dp),
            )
        }
        Spacer(Modifier.height(10.dp))
        PaperCard {
            KickerText("Category probabilities")
            r.categoryProbs.forEach { (k, v) -> ProbabilityBar(k, v) }
            Spacer(Modifier.height(10.dp))
            KickerText("Top predictions")
            r.topK.forEach {
                Row(Modifier.padding(vertical = 2.dp)) {
                    Text("${it.crop} - ${it.name}", fontSize = 13.sp, modifier = Modifier.weight(1f))
                    Text("%.1f%%".format(it.probability * 100), fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                }
            }
        }

        // Report
        if (r.id != null) {
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(
                    onClick = { vm.openReport(context, share = false) },
                    enabled = !vm.reportBusy,
                    modifier = Modifier
                        .weight(1f)
                        .height(50.dp),
                ) {
                    if (vm.reportBusy) CircularProgressIndicator(Modifier.size(18.dp), color = Color.White, strokeWidth = 2.dp)
                    else Text("Open PDF report")
                }
                OutlinedButton(
                    onClick = { vm.openReport(context, share = true) },
                    enabled = !vm.reportBusy,
                    modifier = Modifier.height(50.dp),
                ) { Text("Share") }
            }
            vm.error?.let { Text(it, color = Color(0xFFC0392B), fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp)) }
        }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun Section(title: String, accent: Color = Muted) {
    Spacer(Modifier.height(18.dp))
    KickerText(title, colour = accent)
    Spacer(Modifier.height(4.dp))
}
