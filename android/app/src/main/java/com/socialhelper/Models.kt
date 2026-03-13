package com.socialhelper

import com.google.gson.annotations.SerializedName

data class FeedItem(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("url") val url: String,
    @SerializedName("source") val source: String,
    @SerializedName("published_at") val publishedAt: String,
    @SerializedName("summary") val summary: String = "",
    @SerializedName("author") val author: String = "",
    @SerializedName("tags") val tags: List<String> = emptyList(),
    @SerializedName("score") val score: Int = 0,
    @SerializedName("category") val category: String = "general",
    @SerializedName("llm_summary") val llmSummary: String = "",
    @SerializedName("clickbait_score") val clickbaitScore: Float = 0f,
)

data class FeedResponse(
    @SerializedName("total") val total: Int,
    @SerializedName("offset") val offset: Int,
    @SerializedName("limit") val limit: Int,
    @SerializedName("items") val items: List<FeedItem>,
)

data class DigestResponse(
    @SerializedName("digest") val digest: String,
)

data class CategoriesResponse(
    @SerializedName("categories") val categories: List<String>,
)
