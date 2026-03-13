package com.socialhelper

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface SocialHelperApi {

    @GET("/api/feed")
    suspend fun getFeed(
        @Query("limit") limit: Int = 30,
        @Query("offset") offset: Int = 0,
        @Query("category") category: String? = null,
    ): Response<FeedResponse>

    @GET("/api/feed/categories")
    suspend fun getCategories(): Response<CategoriesResponse>

    @GET("/api/digest")
    suspend fun getDigest(): Response<DigestResponse>

    @GET("/health")
    suspend fun health(): Response<Map<String, String>>
}

object ApiClient {

    private var _baseUrl: String = BuildConfig.BACKEND_URL

    var baseUrl: String
        get() = _baseUrl
        set(value) {
            _baseUrl = value
            _instance = null
        }

    private var _instance: SocialHelperApi? = null

    val instance: SocialHelperApi
        get() {
            if (_instance == null) {
                val logging = HttpLoggingInterceptor().apply {
                    level = if (BuildConfig.DEBUG) {
                        HttpLoggingInterceptor.Level.BODY
                    } else {
                        HttpLoggingInterceptor.Level.NONE
                    }
                }
                val client = OkHttpClient.Builder()
                    .addInterceptor(logging)
                    .connectTimeout(30, TimeUnit.SECONDS)
                    .readTimeout(60, TimeUnit.SECONDS)
                    .build()
                _instance = Retrofit.Builder()
                    .baseUrl(_baseUrl.trimEnd('/') + "/")
                    .client(client)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build()
                    .create(SocialHelperApi::class.java)
            }
            return _instance!!
        }
}
