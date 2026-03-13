package com.socialhelper

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {

    private val viewModel: FeedViewModel by viewModels()
    private lateinit var adapter: FeedAdapter
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var recyclerView: RecyclerView
    private lateinit var emptyView: View

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        setSupportActionBar(findViewById(R.id.toolbar))

        swipeRefresh = findViewById(R.id.swipeRefresh)
        recyclerView = findViewById(R.id.recyclerView)
        emptyView = findViewById(R.id.emptyView)

        adapter = FeedAdapter { item ->
            // Open article in browser on tap
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(item.url)))
        }

        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        swipeRefresh.setOnRefreshListener { viewModel.refresh() }

        viewModel.feedState.observe(this) { state ->
            when (state) {
                is UiState.Loading -> {
                    swipeRefresh.isRefreshing = true
                    emptyView.visibility = View.GONE
                }
                is UiState.Success -> {
                    swipeRefresh.isRefreshing = false
                    adapter.submitList(state.data)
                    emptyView.visibility = if (state.data.isEmpty()) View.VISIBLE else View.GONE
                }
                is UiState.Error -> {
                    swipeRefresh.isRefreshing = false
                    Toast.makeText(this, state.message, Toast.LENGTH_LONG).show()
                    emptyView.visibility = View.VISIBLE
                }
            }
        }

        viewModel.loadCategories()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_digest -> {
                startActivity(Intent(this, DigestActivity::class.java))
                true
            }
            R.id.action_refresh -> {
                viewModel.refresh()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}
