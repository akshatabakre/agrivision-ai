package com.agrivision.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.agrivision.app.AppViewModel
import com.agrivision.app.Connection

@Composable
fun SettingsScreen(vm: AppViewModel) {
    var address by rememberSaveable { mutableStateOf(vm.serverUrl) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        KickerText("Settings")
        Text("Connect to the laptop", style = SerifTitle.copy(fontSize = 26.sp))
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            address, { address = it }, Modifier.fillMaxWidth(),
            label = { Text("Server address") },
            placeholder = { Text("http://192.168.x.x:8000") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
            supportingText = { Text("Shown in the START_MOBILE_SERVER window on the laptop") },
        )
        Button(
            onClick = { vm.saveServer(address); address = vm.serverUrl },
            enabled = address.isNotBlank() && vm.connection != Connection.Checking,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp)
                .height(50.dp),
        ) { Text("Save & test connection") }

        Spacer(Modifier.height(12.dp))
        when (val c = vm.connection) {
            Connection.Unknown -> {}
            Connection.Checking -> Text("Connecting ...", color = Muted)
            is Connection.Ok -> Text(
                "✓ Connected - model loaded (server v${c.version}). ${vm.crops.size} crops supported.",
                color = Color(0xFF2E7D32), fontSize = 15.sp,
            )
            is Connection.Failed -> Text(c.message, color = Color(0xFFC0392B), fontSize = 14.sp)
        }

        Spacer(Modifier.height(20.dp))
        PaperCard {
            KickerText("How to connect")
            listOf(
                "Turn on the phone's mobile hotspot.",
                "Connect the laptop to that hotspot.",
                "On the laptop, double-click START_MOBILE_SERVER.bat in the project folder.",
                "Type the address it shows (e.g. http://192.168.43.20:8000) above and tap Save & test.",
                "If it fails: allow Python through Windows Firewall, or set the hotspot network to Private on the laptop.",
            ).forEachIndexed { i, s -> Bullet(s, "%02d".format(i + 1), Leaf) }
        }
    }
}
