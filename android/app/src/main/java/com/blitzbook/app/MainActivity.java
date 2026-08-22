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

public class MainActivity extends Activity {
    private static final String HOME_URL = "https://nfl-all-time.vercel.app/";
    private static final String HOST = "nfl-all-time.vercel.app";
    private WebView webView;
    private ProgressBar progressBar;

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

        configureWebView();
        navHome.setOnClickListener(v -> goHome());
        navTeams.setOnClickListener(v -> jumpTo("teams"));
        navGames.setOnClickListener(v -> jumpTo("live"));
        navUniverse.setOnClickListener(v -> jumpTo("universe"));

        if (savedInstanceState == null) webView.loadUrl(HOME_URL);
        else webView.restoreState(savedInstanceState);
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
        s.setUserAgentString(s.getUserAgentString() + " BlitzbookAndroid/1.0 Mobile");

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
                injectMobileAppMode();
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

    private void injectMobileAppMode() {
        String js = "(function(){" +
            "var vp=document.querySelector('meta[name=viewport]');if(!vp){vp=document.createElement('meta');vp.name='viewport';document.head.appendChild(vp);}vp.content='width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover';" +
            "document.documentElement.classList.add('bb-apk-mobile');" +
            "var st=document.getElementById('bb-apk-style');if(!st){st=document.createElement('style');st.id='bb-apk-style';document.head.appendChild(st);}" +
            "st.textContent=`" + mobileCss().replace("`", "\\`") + "`;" +
            "})();";
        webView.evaluateJavascript(js, null);
    }

    private String mobileCss() {
        return "html,body{min-width:0!important;width:100%!important;max-width:100%!important;overflow-x:hidden!important}" +
            "body{font-size:14px!important}" +
            ".container{width:100%!important;max-width:100%!important;padding-left:14px!important;padding-right:14px!important}" +
            ".topnav{display:none!important}" +
            ".hero{min-height:0!important;padding:30px 0 26px!important}" +
            ".hero h1{font-size:50px!important;line-height:.92!important;margin-bottom:14px!important}" +
            ".hero-sub{font-size:12px!important;line-height:1.5!important;max-width:340px!important}" +
            ".hero-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}" +
            ".hero-actions .hero-btn{min-height:44px!important;font-size:9px!important;padding:10px!important}" +
            ".hero-actions .hero-btn:nth-child(n+3){display:none!important}" +
            ".section{padding:30px 0!important}.section-title{font-size:28px!important}.section-subtitle{font-size:11px!important}" +
            "#teams .filter-divider,#teams .filter-group{display:none!important}" +
            "#teams .filter-bar{display:grid!important;grid-template-columns:1fr auto!important;gap:8px!important;padding:9px!important}" +
            "#teams .team-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:9px!important}" +
            "#teams .team-card,#teams .team-card-inner,#teams .team-card-face{height:144px!important;min-height:144px!important}" +
            "#teams .team-card-inner{transform:none!important;transition:none!important;transform-style:flat!important}" +
            "#teams .team-card-back{display:none!important}" +
            "#teams .team-card-face{position:relative!important;padding:12px!important}" +
            "#divisions{display:none!important}" +
            "#universe .franchise-universe-tabs,#universe .franchise-ranking-signal,#universe .team-comparison,#universe .comparison-center,#universe [class*=comparison]{display:none!important}" +
            "#universe .franchise-universe-grid{display:block!important}" +
            "#universe .franchise-universe-card{display:none!important}" +
            "#universe .franchise-universe-card-wide{display:block!important;width:100%!important}" +
            "#universe .franchise-universe-table-wrap{max-height:420px!important;overflow:auto!important}" +
            "#live .live-header{padding:12px!important;display:flex!important;flex-wrap:wrap!important;gap:8px!important}" +
            "#live .live-tabs{width:100%!important;display:grid!important;grid-template-columns:repeat(3,1fr)!important;gap:5px!important}" +
            "#live .live-tab{min-height:40px!important}" +
            "#season2026 .season-2026-kpis{display:none!important}" +
            "#season2026 .season-2026-grid{display:block!important}" +
            "#season2026 .season-2026-grid>.season-2026-card:first-child{display:none!important}" +
            "#season2026 .season-2026-grid>.season-2026-card:last-child{width:100%!important}" +
            "*{max-width:100%}";
    }

    private void goHome() {
        String u = webView.getUrl();
        if (u == null || !u.startsWith(HOME_URL)) webView.loadUrl(HOME_URL);
        else webView.evaluateJavascript("window.scrollTo({top:0,behavior:'smooth'})", null);
    }

    private void jumpTo(String id) {
        String u = webView.getUrl();
        if (u == null || !u.startsWith(HOME_URL)) {
            webView.loadUrl(HOME_URL + "#" + id);
            return;
        }
        String js = "(function(){var e=document.getElementById('" + id + "');if(e)e.scrollIntoView({behavior:'smooth',block:'start'});})();";
        webView.evaluateJavascript(js, null);
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }
}
