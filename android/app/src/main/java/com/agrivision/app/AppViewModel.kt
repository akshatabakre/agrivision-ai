package com.agrivision.app

import android.app.Application
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.FileProvider
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.agrivision.app.data.AgriVisionApi
import com.agrivision.app.data.DiagnosisResult
import com.agrivision.app.data.FieldContext
import com.agrivision.app.data.HistoryItem
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File
import kotlin.math.max

enum class Tab { Diagnose, History, Settings }

sealed interface Connection {
    data object Unknown : Connection
    data object Checking : Connection
    data class Ok(val version: String) : Connection
    data class Failed(val message: String) : Connection
}

class AppViewModel(app: Application) : AndroidViewModel(app) {

    private val prefs = app.getSharedPreferences("agrivision", Context.MODE_PRIVATE)

    var serverUrl by mutableStateOf(prefs.getString("server_url", "") ?: "")
        private set
    var connection by mutableStateOf<Connection>(Connection.Unknown)
        private set
    var crops by mutableStateOf<List<String>>(emptyList())
        private set

    var tab by mutableStateOf(if (serverUrl.isBlank()) Tab.Settings else Tab.Diagnose)
    var preview by mutableStateOf<Bitmap?>(null)
        private set
    private var jpeg: ByteArray? = null
    var context by mutableStateOf(FieldContext())

    var busy by mutableStateOf(false)
        private set
    var error by mutableStateOf<String?>(null)
    var result by mutableStateOf<DiagnosisResult?>(null)

    var history by mutableStateOf<List<HistoryItem>>(emptyList())
        private set
    var historyLoading by mutableStateOf(false)
        private set
    var historyError by mutableStateOf<String?>(null)
        private set
    var reportBusy by mutableStateOf(false)
        private set

    private fun api() = AgriVisionApi(serverUrl)

    init {
        if (serverUrl.isNotBlank()) testConnection()
    }

    fun saveServer(input: String) {
        serverUrl = AgriVisionApi.normalise(input)
        prefs.edit().putString("server_url", serverUrl).apply()
        testConnection()
    }

    fun testConnection() {
        if (serverUrl.isBlank()) return
        connection = Connection.Checking
        viewModelScope.launch {
            connection = try {
                val h = api().health()
                crops = runCatching { api().crops() }.getOrDefault(emptyList())
                if (h.optBoolean("model_loaded")) Connection.Ok(h.optString("version"))
                else Connection.Failed("Server is running but no trained model was found.")
            } catch (e: Exception) {
                Connection.Failed(e.message ?: "Connection failed")
            }
        }
    }

    /** Decode (applying EXIF rotation), downscale and re-encode the photo for upload. */
    fun onImagePicked(uri: Uri) {
        error = null
        result = null
        viewModelScope.launch {
            try {
                val (bmp, bytes) = withContext(Dispatchers.IO) {
                    val src = ImageDecoder.createSource(getApplication<Application>().contentResolver, uri)
                    val bmp = ImageDecoder.decodeBitmap(src) { decoder, info, _ ->
                        decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                        val longest = max(info.size.width, info.size.height)
                        if (longest > 1600) {
                            val scale = 1600f / longest
                            decoder.setTargetSize(
                                (info.size.width * scale).toInt(), (info.size.height * scale).toInt()
                            )
                        }
                    }
                    val out = ByteArrayOutputStream()
                    bmp.compress(Bitmap.CompressFormat.JPEG, 92, out)
                    bmp to out.toByteArray()
                }
                preview = bmp
                jpeg = bytes
            } catch (e: Exception) {
                error = "Could not open that image: ${e.message}"
            }
        }
    }

    val hasImage get() = jpeg != null

    fun analyze() {
        val bytes = jpeg ?: return
        busy = true
        error = null
        viewModelScope.launch {
            try {
                result = api().analyze(bytes, context)
            } catch (e: Exception) {
                error = e.message
            } finally {
                busy = false
            }
        }
    }

    fun loadHistory() {
        historyLoading = true
        historyError = null
        viewModelScope.launch {
            try {
                history = api().history()
            } catch (e: Exception) {
                historyError = e.message
            } finally {
                historyLoading = false
            }
        }
    }

    fun openDiagnosis(id: Int) {
        historyLoading = true
        viewModelScope.launch {
            try {
                result = api().diagnosis(id)
            } catch (e: Exception) {
                historyError = e.message
            } finally {
                historyLoading = false
            }
        }
    }

    /** Download the PDF report and open it (or share it if no PDF viewer is installed). */
    fun openReport(activity: Context, share: Boolean) {
        val id = result?.id ?: return
        reportBusy = true
        viewModelScope.launch {
            try {
                val pdf = api().reportPdf(id)
                val file = withContext(Dispatchers.IO) {
                    File(activity.cacheDir, "reports").apply { mkdirs() }
                        .resolve("agrivision_report_$id.pdf").apply { writeBytes(pdf) }
                }
                val uri = FileProvider.getUriForFile(activity, "${activity.packageName}.files", file)
                val shareIntent = Intent.createChooser(
                    Intent(Intent.ACTION_SEND).setType("application/pdf")
                        .putExtra(Intent.EXTRA_STREAM, uri)
                        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION),
                    "Share crop health report"
                )
                if (share) {
                    activity.startActivity(shareIntent)
                } else {
                    try {
                        activity.startActivity(
                            Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/pdf")
                                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                        )
                    } catch (e: ActivityNotFoundException) {
                        activity.startActivity(shareIntent)
                    }
                }
            } catch (e: Exception) {
                error = e.message
            } finally {
                reportBusy = false
            }
        }
    }

    /** A fresh file the camera app writes the photo into. */
    fun newCaptureUri(): Uri {
        val app = getApplication<Application>()
        val dir = File(app.cacheDir, "images").apply { mkdirs() }
        val file = File(dir, "capture_${System.currentTimeMillis()}.jpg")
        return FileProvider.getUriForFile(app, "${app.packageName}.files", file)
    }
}
