package com.socialhelper

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView

class FeedAdapter(
    private val onItemClick: (FeedItem) -> Unit,
) : ListAdapter<FeedItem, FeedAdapter.ViewHolder>(DIFF_CALLBACK) {

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvTitle: TextView = itemView.findViewById(R.id.tvTitle)
        private val tvSource: TextView = itemView.findViewById(R.id.tvSource)
        private val tvSummary: TextView = itemView.findViewById(R.id.tvSummary)
        private val tvCategory: TextView = itemView.findViewById(R.id.tvCategory)
        private val tvClickbait: TextView = itemView.findViewById(R.id.tvClickbait)

        fun bind(item: FeedItem) {
            tvTitle.text = item.title
            tvSource.text = "${item.source} · ${item.publishedAt.take(10)}"
            tvSummary.text = item.llmSummary.ifBlank { item.summary }.take(200)
            tvCategory.text = item.category.uppercase()
            tvClickbait.visibility = if (item.clickbaitScore > 0.5f) View.VISIBLE else View.GONE
            itemView.setOnClickListener { onItemClick(item) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_feed, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    companion object {
        private val DIFF_CALLBACK = object : DiffUtil.ItemCallback<FeedItem>() {
            override fun areItemsTheSame(old: FeedItem, new: FeedItem) = old.id == new.id
            override fun areContentsTheSame(old: FeedItem, new: FeedItem) = old == new
        }
    }
}
