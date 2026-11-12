package com.agrivision.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.agrivision.app.AppViewModel

@Composable
fun HistoryScreen(vm: AppViewModel) {
    LaunchedEffect(Unit) { vm.loadHistory() }
    val items = vm.history
    val ok = items.filter { it.status == "ok" }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                KickerText("Monitor → prevent")
                Text("Diagnosis history", style = SerifTitle.copy(fontSize = 26.sp))
            }
            IconButton(onClick = vm::loadHistory) { Icon(Icons.Filled.Refresh, "Refresh") }
        }
        if (vm.historyLoading) LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical = 6.dp))
        vm.historyError?.let { Text(it, color = Color(0xFFC0392B), fontSize = 13.sp) }

        if (items.isNotEmpty()) {
            Row(Modifier.padding(vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                Stat("Diagnoses", items.size.toString())
                Stat("Problems", ok.count { it.category != "healthy" }.toString())
                Stat("Avg health", ok.mapNotNull { it.healthScore }.average().takeIf { !it.isNaN() }
                    ?.let { "%.0f".format(it) } ?: "-")
            }
        } else if (!vm.historyLoading && vm.historyError == null) {
            Text(
                "No diagnoses yet. Analyse a leaf on the Diagnose tab - add a field name to track it over time.",
                color = Muted, modifier = Modifier.padding(top = 16.dp),
            )
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(items, key = { it.id }) { h ->
                val colour = if (h.status == "ok") severityColour(h.severity) else severityColour("Unknown")
                PaperCard(Modifier.clickable { vm.openDiagnosis(h.id) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            KickerText(
                                "#${h.id} · ${h.createdAt.take(16).replace('T', ' ')}" +
                                    (h.fieldId?.let { " · $it" } ?: "")
                            )
                            Text(h.displayName, style = SerifTitle.copy(fontSize = 18.sp, color = colour))
                            Text("${h.crop} · ${h.severity} · %.0f%% confidence".format(h.confidence * 100),
                                fontSize = 13.sp, color = Muted)
                        }
                        Text(
                            h.healthScore?.toString() ?: "--",
                            style = SerifTitle.copy(fontSize = 26.sp, color = colour),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun Stat(label: String, value: String) = Column {
    KickerText(label)
    Text(value, style = SerifTitle.copy(fontSize = 24.sp), fontFamily = FontFamily.Serif)
}
