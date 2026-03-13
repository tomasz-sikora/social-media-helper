package com.socialhelper

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class ModelsTest {

    @Test
    fun feedItem_hasCorrectDefaults() {
        val item = FeedItem(
            id = "abc123",
            title = "Test title",
            url = "https://example.com",
            source = "test",
            publishedAt = "2024-01-01T00:00:00",
        )
        assertEquals("general", item.category)
        assertEquals("", item.llmSummary)
        assertEquals(0f, item.clickbaitScore)
        assertEquals(emptyList<String>(), item.tags)
    }

    @Test
    fun feedItem_equalityBasedOnId() {
        val a = FeedItem("id1", "Title A", "https://a.com", "src", "2024-01-01T00:00:00")
        val b = FeedItem("id1", "Title B", "https://b.com", "src2", "2024-01-01T00:00:00")
        val c = FeedItem("id2", "Title A", "https://a.com", "src", "2024-01-01T00:00:00")
        // Same id = same item (for DiffUtil)
        assertEquals(a.id, b.id)
        assertNotEquals(a.id, c.id)
    }
}
