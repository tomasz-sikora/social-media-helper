package com.socialhelper

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch

sealed class UiState<out T> {
    object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}

class FeedViewModel : ViewModel() {

    private val _feedState = MutableLiveData<UiState<List<FeedItem>>>(UiState.Loading)
    val feedState: LiveData<UiState<List<FeedItem>>> = _feedState

    private val _categories = MutableLiveData<List<String>>(emptyList())
    val categories: LiveData<List<String>> = _categories

    private var currentCategory: String? = null
    private var currentOffset = 0
    private val allItems = mutableListOf<FeedItem>()

    init {
        loadFeed()
    }

    fun loadFeed(category: String? = currentCategory, refresh: Boolean = false) {
        currentCategory = category
        if (refresh) {
            currentOffset = 0
            allItems.clear()
        }
        _feedState.value = UiState.Loading
        viewModelScope.launch {
            try {
                val resp = ApiClient.instance.getFeed(
                    limit = 30,
                    offset = currentOffset,
                    category = category,
                )
                if (resp.isSuccessful) {
                    val body = resp.body() ?: return@launch
                    allItems.addAll(body.items)
                    currentOffset += body.items.size
                    _feedState.value = UiState.Success(allItems.toList())
                } else {
                    _feedState.value = UiState.Error("Server error: ${resp.code()}")
                }
            } catch (e: Exception) {
                _feedState.value = UiState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun loadCategories() {
        viewModelScope.launch {
            try {
                val resp = ApiClient.instance.getCategories()
                if (resp.isSuccessful) {
                    _categories.value = resp.body()?.categories ?: emptyList()
                }
            } catch (_: Exception) { /* ignore */ }
        }
    }

    fun refresh() = loadFeed(refresh = true)
}
