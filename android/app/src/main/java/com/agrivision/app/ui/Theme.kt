package com.agrivision.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Same palette as the Streamlit app / project slides
val Cream = Color(0xFFF3EBDD)
val Paper = Color(0xFFFAF5EC)
val Ink = Color(0xFF221C16)
val InkCard = Color(0xFF1F1A15)
val Muted = Color(0xFF8A7D6E)
val Line = Color(0xFFE3D8C6)
val Leaf = Color(0xFF3A6B35)
val NoteBg = Color(0xFFFFF7E6)

val SeverityColour = mapOf(
    "Healthy" to Color(0xFF2E7D32),
    "Mild" to Color(0xFFB8961A),
    "Moderate" to Color(0xFFD9822B),
    "Severe" to Color(0xFFC0392B),
    "Unknown" to Color(0xFF7A6F64),
)

val RiskText = mapOf(
    "Healthy" to "Low Risk", "Mild" to "Low-Moderate Risk", "Moderate" to "Moderate Risk",
    "Severe" to "High Risk", "Unknown" to "Re-capture",
)

fun severityColour(s: String) = SeverityColour[s] ?: SeverityColour.getValue("Unknown")

fun confidenceColour(c: Double) = when {
    c >= 0.85 -> Color(0xFF2E7D32)
    c >= 0.60 -> Color(0xFFB8961A)
    else -> Color(0xFFC0392B)
}

val Kicker = TextStyle(fontFamily = FontFamily.Monospace, fontSize = 11.sp, letterSpacing = 1.5.sp, color = Muted)
val SerifTitle = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold)

@Composable
fun AgriVisionTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = Leaf,
            onPrimary = Color.White,
            secondary = Color(0xFFD9822B),
            background = Cream,
            onBackground = Ink,
            surface = Paper,
            onSurface = Ink,
            surfaceVariant = Paper,
            surfaceContainer = Paper,
            outline = Line,
        ),
        content = content,
    )
}
