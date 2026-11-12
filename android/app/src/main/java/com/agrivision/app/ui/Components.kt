package com.agrivision.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun KickerText(text: String, modifier: Modifier = Modifier, colour: Color = Muted) =
    Text(text.uppercase(), style = Kicker.copy(color = colour), modifier = modifier)

@Composable
fun PaperCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) = Column(
    modifier
        .fillMaxWidth()
        .clip(RoundedCornerShape(6.dp))
        .background(Paper)
        .border(1.dp, Line, RoundedCornerShape(6.dp))
        .padding(16.dp),
    content = content,
)

@Composable
fun DarkCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) = Column(
    modifier
        .fillMaxWidth()
        .clip(RoundedCornerShape(6.dp))
        .background(InkCard)
        .padding(16.dp),
    content = content,
)

@Composable
fun Chip(text: String, colour: Color) = Text(
    text.uppercase(),
    color = colour,
    fontFamily = FontFamily.Monospace,
    fontSize = 11.sp,
    modifier = Modifier
        .border(1.dp, colour, RoundedCornerShape(50))
        .padding(horizontal = 10.dp, vertical = 2.dp),
)

/** Health score bar with the 0-39 / 40-69 / 70-89 / 90-100 scale from slide 8. */
@Composable
fun HealthBar(score: Int?, colour: Color) {
    Box(
        Modifier
            .fillMaxWidth()
            .height(14.dp)
            .clip(RoundedCornerShape(3.dp))
            .background(Color(0xFF3A322A))
    ) {
        Box(
            Modifier
                .fillMaxWidth(((score ?: 0) / 100f).coerceIn(0f, 1f))
                .height(14.dp)
                .background(colour)
        )
    }
    Row(Modifier.fillMaxWidth().padding(top = 4.dp)) {
        listOf("0 SEVERE", "40 MOD.", "70 MILD", "90 HEALTHY").forEach {
            Text(it, style = Kicker.copy(fontSize = 9.sp, color = Color(0xFFA39482)), modifier = Modifier.weight(1f))
        }
    }
}

@Composable
fun ProbabilityBar(label: String, value: Double) {
    Column(Modifier.padding(vertical = 3.dp)) {
        Row {
            Text(label, fontSize = 13.sp, modifier = Modifier.weight(1f))
            Text("%.0f%%".format(value * 100), fontSize = 13.sp, fontFamily = FontFamily.Monospace)
        }
        Box(
            Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(Line)
        ) {
            Box(
                Modifier
                    .fillMaxWidth(value.toFloat().coerceIn(0f, 1f))
                    .height(6.dp)
                    .background(Leaf)
            )
        }
    }
}

@Composable
fun Bullet(text: String, prefix: String = "·", prefixColour: Color = Ink) = Row(
    Modifier
        .fillMaxWidth()
        .padding(vertical = 5.dp)
) {
    Text(prefix, color = prefixColour, fontFamily = FontFamily.Monospace, modifier = Modifier.width(30.dp))
    Text(text, fontSize = 15.sp)
}

@Composable
fun Note(text: String) = Row(
    Modifier
        .fillMaxWidth()
        .padding(vertical = 4.dp)
        .height(IntrinsicSize.Min)
        .clip(RoundedCornerShape(3.dp))
        .background(NoteBg)
) {
    Box(Modifier.width(3.dp).fillMaxHeight().background(Color(0xFFD9822B)))
    Text(text, fontSize = 14.sp, modifier = Modifier.padding(10.dp))
}
