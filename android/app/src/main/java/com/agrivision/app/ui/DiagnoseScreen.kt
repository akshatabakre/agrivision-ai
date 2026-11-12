package com.agrivision.app.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.agrivision.app.AppViewModel
import com.agrivision.app.Connection
import com.agrivision.app.Tab

val GROWTH_STAGES = listOf("Not specified", "Seedling", "Vegetative", "Flowering", "Fruiting")

@Composable
fun AppHeader() {
    Column(Modifier.padding(bottom = 12.dp)) {
        KickerText("Crop health intelligence")
        Text("AgriVision AI", style = SerifTitle.copy(fontSize = 34.sp))
        Text(
            "Detect crop diseases, pest damage and nutrient deficiencies from a single photograph.",
            color = Color(0xFF6B5F52), fontSize = 14.sp,
        )
    }
}

@Composable
fun DiagnoseScreen(vm: AppViewModel) {
    var captureUri by rememberSaveable { mutableStateOf<Uri?>(null) }
    var showContext by rememberSaveable { mutableStateOf(false) }

    val pickImage = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        uri?.let(vm::onImagePicked)
    }
    val takePhoto = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { saved ->
        if (saved) captureUri?.let(vm::onImagePicked)
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        AppHeader()

        when (val c = vm.connection) {
            is Connection.Failed -> PaperCard(Modifier.padding(bottom = 12.dp)) {
                Text("Not connected to the AgriVision server", color = Color(0xFFC0392B), fontSize = 15.sp)
                Text(c.message, fontSize = 13.sp, color = Muted)
                TextButton(onClick = { vm.tab = Tab.Settings }) { Text("Open Settings") }
            }
            else -> {}
        }

        KickerText("01 · Capture or upload a crop image")
        Spacer(Modifier.height(8.dp))
        Box(
            Modifier
                .fillMaxWidth()
                .aspectRatio(4f / 3f)
                .clip(RoundedCornerShape(6.dp))
                .background(Paper)
                .border(1.dp, Line, RoundedCornerShape(6.dp))
                .clickable { pickImage.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
            contentAlignment = Alignment.Center,
        ) {
            val bmp = vm.preview
            if (bmp != null) {
                Image(bmp.asImageBitmap(), "Selected leaf", Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            } else {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(24.dp)) {
                    KickerText("No image yet")
                    Text(
                        "Photograph one leaf in daylight, filling most of the frame.",
                        textAlign = TextAlign.Center, color = Muted, fontSize = 14.sp,
                    )
                }
            }
        }
        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(
                onClick = { vm.newCaptureUri().also { captureUri = it; takePhoto.launch(it) } },
                modifier = Modifier.weight(1f),
            ) { Text("Take photo") }
            OutlinedButton(
                onClick = { pickImage.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                modifier = Modifier.weight(1f),
            ) { Text("From gallery") }
        }

        Spacer(Modifier.height(14.dp))
        Dropdown(
            label = "Crop",
            options = listOf("Auto-detect") + vm.crops,
            selected = vm.context.crop ?: "Auto-detect",
            onSelect = { vm.context = vm.context.copy(crop = it.takeIf { c -> c != "Auto-detect" }) },
        )
        Text(
            "Telling the model the crop removes confusion with other crops.",
            fontSize = 12.sp, color = Muted, modifier = Modifier.padding(top = 2.dp),
        )

        TextButton(onClick = { showContext = !showContext }, modifier = Modifier.padding(top = 4.dp)) {
            Text((if (showContext) "▾ " else "▸ ") + "Field context (optional - makes advice specific to your farm)")
        }
        if (showContext) FieldContextForm(vm)

        vm.error?.let {
            Text(it, color = Color(0xFFC0392B), fontSize = 14.sp, modifier = Modifier.padding(vertical = 8.dp))
        }

        Button(
            onClick = vm::analyze,
            enabled = vm.hasImage && !vm.busy,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp)
                .height(52.dp),
        ) {
            if (vm.busy) {
                CircularProgressIndicator(Modifier.size(20.dp), color = Color.White, strokeWidth = 2.dp)
                Spacer(Modifier.size(10.dp))
                Text("Analysing ...")
            } else {
                Text("Analyse crop", fontSize = 17.sp)
            }
        }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun FieldContextForm(vm: AppViewModel) {
    val c = vm.context
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(
            c.fieldId, { vm.context = c.copy(fieldId = it) }, Modifier.fillMaxWidth(),
            label = { Text("Field / plot name") }, placeholder = { Text("e.g. North plot") }, singleLine = true,
            supportingText = { Text("Tracks history and detects recurring outbreaks") },
        )
        OutlinedTextField(
            c.region, { vm.context = c.copy(region = it) }, Modifier.fillMaxWidth(),
            label = { Text("Region / state") }, placeholder = { Text("e.g. Maharashtra") }, singleLine = true,
        )
        Dropdown("Growth stage", GROWTH_STAGES, c.growthStage) { vm.context = c.copy(growthStage = it) }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Add weather / IoT sensor readings", Modifier.weight(1f))
            Switch(c.useSensors, { vm.context = c.copy(useSensors = it) })
        }
        if (c.useSensors) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                NumberField("Temperature (C)", c.temperature, Modifier.weight(1f)) { vm.context = c.copy(temperature = it) }
                NumberField("Humidity (%)", c.humidity, Modifier.weight(1f)) { vm.context = c.copy(humidity = it) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                NumberField("Soil moisture (%)", c.soilMoisture, Modifier.weight(1f)) { vm.context = c.copy(soilMoisture = it) }
                NumberField("Soil pH", c.soilPh, Modifier.weight(1f)) { vm.context = c.copy(soilPh = it) }
            }
        }
    }
}

@Composable
private fun NumberField(label: String, value: String, modifier: Modifier, onChange: (String) -> Unit) =
    OutlinedTextField(
        value, onChange, modifier, label = { Text(label, fontSize = 12.sp) }, singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
    )

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun Dropdown(label: String, options: List<String>, selected: String, onSelect: (String) -> Unit) {
    var expanded by rememberSaveable { mutableStateOf(false) }
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
        OutlinedTextField(
            value = selected,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(MenuAnchorType.PrimaryNotEditable),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach {
                DropdownMenuItem(text = { Text(it) }, onClick = { onSelect(it); expanded = false })
            }
        }
    }
}
