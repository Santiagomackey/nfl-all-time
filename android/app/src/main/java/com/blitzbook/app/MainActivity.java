package com.blitzbook.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ProgressBar;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public class MainActivity extends Activity {
    private static final String HOME_URL = "https://nfl-all-time.vercel.app/";
    private static final String HOST = "nfl-all-time.vercel.app";
    private WebView webView;
    private ProgressBar progressBar;
    private String mobileScript = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);
        Button navHome = findViewById(R.id.navHome);
        Button navTeams = findViewById(R.id.navTeams);
        Button navGames = findViewById(R.id.navGames);
        Button navUniverse = findViewById(R.id.navUniverse);

        mobileScript = readAsset("app-mobile.js");
        configureWebView();

        navHome.setOnClickListener(v -> goHome());
        navTeams.setOnClickListener(v -> jumpTo("teams"));
        navGames.setOnClickListener(v -> jumpTo("live"));
        navUniverse.setOnClickListener(v -> jumpTo("universe"));

        if (savedInstanceState == null) webView.loadUrl(HOME_URL);
        else webView.restoreState(savedInstanceState);
    }

    private String readAsset(String name) {
        StringBuilder out = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(getAssets().open(name)))) {
            String line;
            while ((line = br.readLine()) != null) out.append(line).append('\n');
        } catch (Exception ignored) {}
        return out.toString();
    }

    private void configureWebView() {
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setLoadsImagesAutomatically(true);
        s.setUseWideViewPort(false);
        s.setLoadWithOverviewMode(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setSupportZoom(false);
        s.setMediaPlaybackRequiresUserGesture(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setUserAgentString(s.getUserAgentString() + " BlitzbookAndroid/2.0 Mobile");

        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view, int newProgress) {
                progressBar.setProgress(newProgress);
                progressBar.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override public void onPageStarted(WebView view, String url, Bitmap favicon) {
                progressBar.setVisibility(View.VISIBLE);
            }

            @Override public void onPageFinished(WebView view, String url) {
                if (mobileScript != null && !mobileScript.isEmpty()) {
                    view.evaluateJavascript(mobileScript, null);
                }
            }

            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String host = uri.getHost();
                if (host != null && (host.equals(HOST) || host.endsWith(".vercel.app"))) return false;
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    return true;
                } catch (Exception ignored) {
                    return false;
                }
            }
        });
    }

    private void closeTeamOverlayThen(String fallbackJs) {
        String js = "(function(){if(document.getElementById('bb-team-mobile')){if(window.bbCloseTeam)window.bbCloseTeam();return true;}return false;})()";
        webView.evaluateJavascript(js, result -> {
            if (!"true".equals(result) && fallbackJs != null) {
                webView.evaluateJavascript(fallbackJs, null);
            }
        });
    }

    private void goHome() {
        String u = webView.getUrl();
        if (u == null || !u.startsWith(HOME_URL)) {
            webView.loadUrl(HOME_URL);
            return;
        }
        closeTeamOverlayThen("window.scrollTo({top:0,behavior:'smooth'})");
    }

    private void jumpTo(String id) {
        String u = webView.getUrl();
        if (u == null || !u.startsWith(HOME_URL)) {
            webView.loadUrl(HOME_URL + "#" + id);
            return;
        }
        String js = "(function(){var e=document.getElementById('" + id + "');if(e)e.scrollIntoView({behavior:'smooth',block:'start'});})();";
        closeTeamOverlayThen(js);
    }

    @Override public void onBackPressed() {
        String js = "(function(){if(document.getElementById('bb-team-mobile')){if(window.bbCloseTeam)window.bbCloseTeam();return true;}return false;})()";
        webView.evaluateJavascript(js, result -> {
            if ("true".equals(result)) return;
            if (webView.canGoBack()) webView.goBack();
            else MainActivity.super.onBackPressed();
        });
    }

    @Override protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }
}
