package com.socialhelper

import android.os.Bundle
import android.view.View
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class DigestActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_digest)
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            title = getString(R.string.digest_title)
        }

        val progressBar: ProgressBar = findViewById(R.id.progressBar)
        val tvDigest: TextView = findViewById(R.id.tvDigest)

        progressBar.visibility = View.VISIBLE
        tvDigest.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val resp = ApiClient.instance.getDigest()
                progressBar.visibility = View.GONE
                if (resp.isSuccessful) {
                    tvDigest.text = resp.body()?.digest ?: "No digest available."
                    tvDigest.visibility = View.VISIBLE
                } else {
                    Toast.makeText(this@DigestActivity, "Error: ${resp.code()}", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                progressBar.visibility = View.GONE
                Toast.makeText(this@DigestActivity, e.message ?: "Unknown error", Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
