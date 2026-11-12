package com.agrivision.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.agrivision.app.ui.AgriVisionTheme
import com.agrivision.app.ui.Cream
import com.agrivision.app.ui.DiagnoseScreen
import com.agrivision.app.ui.HistoryScreen
import com.agrivision.app.ui.ResultScreen
import com.agrivision.app.ui.SettingsScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AgriVisionTheme { App(viewModel()) }
        }
    }
}

@Composable
fun App(vm: AppViewModel) {
    val result = vm.result
    BackHandler(enabled = result != null) { vm.result = null }

    Scaffold(
        containerColor = Cream,
        bottomBar = {
            NavigationBar(containerColor = Cream) {
                listOf(
                    Triple(Tab.Diagnose, "Diagnose", Icons.Filled.Search),
                    Triple(Tab.History, "History", Icons.AutoMirrored.Filled.List),
                    Triple(Tab.Settings, "Settings", Icons.Filled.Settings),
                ).forEach { (tab, label, icon) ->
                    NavigationBarItem(
                        selected = vm.tab == tab,
                        onClick = { vm.tab = tab; vm.result = null; vm.error = null },
                        icon = { Icon(icon, label) },
                        label = { Text(label) },
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.padding(padding)) {
            when {
                result != null && vm.tab != Tab.Settings -> ResultScreen(vm, result)
                vm.tab == Tab.Diagnose -> DiagnoseScreen(vm)
                vm.tab == Tab.History -> HistoryScreen(vm)
                else -> SettingsScreen(vm)
            }
        }
    }
}
