"""
SEOブログ記事生成アプリのメインStreamlitアプリケーション
"""
import os
import streamlit as st
import json
import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 自作モジュールのインポート
from utils import ClaudeClient, SEOAnalyzer, MarkdownProcessor

# 定数
TARGET_AUDIENCE_OPTIONS = ["初心者", "中級者", "上級者", "一般"]
ARTICLE_LENGTH_OPTIONS = ["短め", "標準", "長め"]

# セッション状態の初期化
def init_session_state():
    """アプリケーションのセッション状態を初期化"""
    if "step" not in st.session_state:
        st.session_state.step = 1  # 1: キーワード入力, 2: タイトル選択, 3: 記事表示
    
    if "main_keyword" not in st.session_state:
        st.session_state.main_keyword = ""
    
    if "related_keywords" not in st.session_state:
        st.session_state.related_keywords = []
    
    if "target_audience" not in st.session_state:
        st.session_state.target_audience = "一般"
    
    if "article_length" not in st.session_state:
        st.session_state.article_length = "標準"
    
    if "generated_titles" not in st.session_state:
        st.session_state.generated_titles = []
        
    if "title_scores" not in st.session_state:
        st.session_state.title_scores = {}
    
    if "selected_title" not in st.session_state:
        st.session_state.selected_title = ""
    
    if "generated_article" not in st.session_state:
        st.session_state.generated_article = ""
    
    if "seo_analysis" not in st.session_state:
        st.session_state.seo_analysis = {}
    
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

# キーワード入力画面
def show_keyword_input():
    """キーワード入力画面を表示"""
    st.markdown("## 1. キーワードを入力")
    
    # API キーの入力（環境変数が設定されていない場合）
    if not st.session_state.api_key:
        st.warning("Claude API キーが設定されていません")
        api_key = st.text_input("Claude API キー", 
                               value=st.session_state.api_key, 
                               type="password",
                               help="Anthropic Claude API キーを入力してください。このキーは保存されません。")
        if api_key:
            st.session_state.api_key = api_key
    
    # キーワード入力フォーム
    main_keyword = st.text_input("メインキーワード", 
                                value=st.session_state.main_keyword,
                                help="記事の主題となるメインキーワードを入力してください")
    
    # 関連キーワード入力（カンマ区切り）
    related_keywords_input = st.text_input("関連キーワード（カンマ区切り）", 
                                         help="関連するキーワードをカンマ区切りで入力してください（任意）")
    
    # ターゲット読者層の選択
    target_audience = st.selectbox("ターゲット読者層", 
                                  options=TARGET_AUDIENCE_OPTIONS,
                                  index=TARGET_AUDIENCE_OPTIONS.index(st.session_state.target_audience),
                                  help="記事のターゲットとなる読者層を選択してください")
    
    # 記事の希望文字数
    article_length = st.selectbox("記事の長さ", 
                                 options=ARTICLE_LENGTH_OPTIONS,
                                 index=ARTICLE_LENGTH_OPTIONS.index(st.session_state.article_length),
                                 help="記事の長さを選択してください")
    
    # フォーム送信ボタン
    if st.button("タイトルを生成", disabled=not main_keyword or not st.session_state.api_key):
        with st.spinner("タイトルを生成中..."):
            # セッション状態を更新
            st.session_state.main_keyword = main_keyword
            
            # 関連キーワードをリストに変換
            if related_keywords_input:
                st.session_state.related_keywords = [kw.strip() for kw in related_keywords_input.split(",") if kw.strip()]
            else:
                st.session_state.related_keywords = []
            
            st.session_state.target_audience = target_audience
            st.session_state.article_length = article_length
            
            try:
                # Claude APIでタイトル生成
                claude_client = ClaudeClient(api_key=st.session_state.api_key)
                titles = claude_client.generate_titles(
                    main_keyword=main_keyword,
                    related_keywords=st.session_state.related_keywords,
                    target_audience=target_audience
                )
                
                if titles and len(titles) > 0:
                    st.session_state.generated_titles = titles
                    
                    # タイトルのSEO評価を取得
                    title_scores = {}
                    for title in titles:
                        title_scores[title] = claude_client.evaluate_seo_title(title, main_keyword)
                    
                    st.session_state.title_scores = title_scores
                    st.session_state.step = 2  # タイトル選択ステップへ
                    st.rerun()
                else:
                    st.error("タイトルの生成に失敗しました。別のキーワードを試してください。")
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

# タイトル選択画面
def show_title_selection():
    """タイトル選択画面を表示"""
    st.markdown("## 2. タイトルを選択")
    
    # 入力情報の表示
    st.markdown(f"**メインキーワード:** {st.session_state.main_keyword}")
    if st.session_state.related_keywords:
        st.markdown(f"**関連キーワード:** {', '.join(st.session_state.related_keywords)}")
    
    st.markdown("### 生成されたタイトル候補")
    
    # タイトル候補の表示とSEOスコア
    selected_title = None
    
    for title in st.session_state.generated_titles:
        score_data = st.session_state.title_scores.get(title, {"score": 0, "comment": "評価なし"})
        score = score_data.get("score", 0)
        
        # スコアに基づいた色設定
        if score >= 80:
            score_color = "green"
        elif score >= 60:
            score_color = "orange"
        else:
            score_color = "red"
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            title_selected = st.radio(
                "タイトル",
                [title],
                key=f"title_{title}",
                label_visibility="collapsed"
            )
            if title_selected:
                selected_title = title
            
            st.markdown(f"SEOコメント: {score_data.get('comment', '評価なし')}")
        
        with col2:
            st.markdown(f"<h3 style='color:{score_color};text-align:center;'>{score}</h3>", unsafe_allow_html=True)
        
        st.divider()
    
    # カスタムタイトル入力オプション
    st.markdown("### タイトルをカスタマイズ")
    custom_title = st.text_input("カスタムタイトル", 
                               value=selected_title if selected_title else "",
                               help="選択したタイトルを編集するか、独自のタイトルを入力できます")
    
    # ナビゲーションボタン
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("戻る"):
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.button("記事を生成", disabled=not custom_title):
            with st.spinner("記事を生成中..."):
                st.session_state.selected_title = custom_title
                try:
                    # Claude APIで記事生成
                    claude_client = ClaudeClient(api_key=st.session_state.api_key)
                    article = claude_client.generate_article(
                        title=custom_title,
                        main_keyword=st.session_state.main_keyword,
                        related_keywords=st.session_state.related_keywords,
                        target_audience=st.session_state.target_audience,
                        length=st.session_state.article_length
                    )
                    
                    if article:
                        st.session_state.generated_article = article
                        
                        # SEO分析を実行
                        seo_analyzer = SEOAnalyzer()
                        keyword_analysis = seo_analyzer.analyze_keyword_density(
                            article, st.session_state.main_keyword
                        )
                        headings_analysis = seo_analyzer.analyze_headings(article)
                        readability_analysis = seo_analyzer.analyze_readability(article)
                        
                        st.session_state.seo_analysis = {
                            "keyword": keyword_analysis,
                            "headings": headings_analysis,
                            "readability": readability_analysis
                        }
                        
                        st.session_state.step = 3  # 記事表示ステップへ
                        st.rerun()
                    else:
                        st.error("記事の生成に失敗しました。別のタイトルを試してください。")
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")

# 記事表示画面
def show_article_view():
    """記事表示画面を表示"""
    st.markdown("## 3. 生成された記事")
    
    # タブの作成
    tab1, tab2, tab3 = st.tabs(["記事プレビュー", "マークダウン", "SEO分析"])
    
    with tab1:
        # HTMLプレビュー表示
        md_processor = MarkdownProcessor()
        html_content = md_processor.convert_to_html(st.session_state.generated_article)
        st.markdown(html_content, unsafe_allow_html=True)
    
    with tab2:
        # マークダウン表示と編集
        st.markdown("### マークダウンエディタ")
        article_text = st.text_area("記事を編集", 
                                  value=st.session_state.generated_article,
                                  height=500)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("記事を更新"):
                st.session_state.generated_article = article_text
                
                # SEO分析を再実行
                seo_analyzer = SEOAnalyzer()
                keyword_analysis = seo_analyzer.analyze_keyword_density(
                    article_text, st.session_state.main_keyword
                )
                headings_analysis = seo_analyzer.analyze_headings(article_text)
                readability_analysis = seo_analyzer.analyze_readability(article_text)
                
                st.session_state.seo_analysis = {
                    "keyword": keyword_analysis,
                    "headings": headings_analysis,
                    "readability": readability_analysis
                }
                
                st.success("記事を更新しました")
                st.rerun()
        
        with col2:
            if st.button("目次を追加"):
                md_processor = MarkdownProcessor()
                article_with_toc = md_processor.add_toc_if_needed(article_text)
                
                if article_with_toc != article_text:
                    st.session_state.generated_article = article_with_toc
                    st.success("目次を追加しました")
                    st.rerun()
                else:
                    st.info("目次の追加は不要か、既に存在しています")
        
        # エクスポートオプション
        st.markdown("### エクスポートオプション")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("クリップボードにコピー"):
                md_processor = MarkdownProcessor()
                success = md_processor.save_to_clipboard(article_text)
                
                if success:
                    st.success("クリップボードにコピーしました")
                else:
                    st.error("クリップボードへのコピーに失敗しました")
        
        with col2:
            # ファイルダウンロード
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            file_name = f"seo_article_{current_date}.md"
            
            st.download_button(
                label="マークダウンファイルをダウンロード",
                data=article_text,
                file_name=file_name,
                mime="text/markdown"
            )
    
    with tab3:
        # SEO分析結果の表示
        st.markdown("### SEO分析")
        
        # キーワード分析
        st.markdown("#### キーワード分析")
        keyword_data = st.session_state.seo_analysis.get("keyword", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("キーワード出現回数", keyword_data.get("keyword_count", 0))
        with col2:
            density = keyword_data.get("density", 0)
            st.metric("キーワード密度", f"{density}%")
        
        st.markdown(f"**推奨事項:** {keyword_data.get('recommendation', '情報なし')}")
        
        # 見出し分析
        st.markdown("#### 見出し構造分析")
        headings_data = st.session_state.seo_analysis.get("headings", {})
        
        if headings_data.get("is_good_structure", False):
            st.success("見出し構造は適切です")
        else:
            if not headings_data.get("has_h1", True):
                st.warning("H1見出し（タイトル）がありません")
            if not headings_data.get("has_h2", True):
                st.warning("H2見出しがありません")
            if headings_data.get("too_many_h1", False):
                st.warning("H1見出しが複数あります（通常は1つが推奨）")
        
        h_counts = headings_data.get("counts", {})
        cols = st.columns(6)
        for i, col in enumerate(cols):
            with col:
                st.metric(f"H{i+1}", h_counts.get(f"h{i+1}", 0))
        
        # 読みやすさ分析
        st.markdown("#### 読みやすさ分析")
        readability_data = st.session_state.seo_analysis.get("readability", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("段落数", readability_data.get("paragraph_count", 0))
        with col2:
            st.metric("文の数", readability_data.get("sentence_count", 0))
        with col3:
            st.metric("長い段落の数", readability_data.get("long_paragraphs_count", 0))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("平均段落長（文字）", round(readability_data.get("avg_paragraph_length", 0), 1))
        with col2:
            st.metric("平均文長（文字）", round(readability_data.get("avg_sentence_length", 0), 1))
        
        if readability_data.get("is_good_readability", False):
            st.success("文章の読みやすさは良好です")
        else:
            st.warning("文章の読みやすさを改善するには、長い段落や文を分割することを検討してください")
    
    # ナビゲーションボタン
    if st.button("新しい記事を作成"):
        # セッション状態をリセット（APIキーは保持）
        api_key = st.session_state.api_key
        st.session_state.clear()
        st.session_state.api_key = api_key
        st.session_state.step = 1
        st.rerun()

# メイン関数
def main():
    """アプリケーションのメインエントリポイント"""
    st.set_page_config(
        page_title="SEOブログ記事生成アプリ",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # サイドバー情報
    with st.sidebar:
        st.title("SEOブログ記事生成アプリ")
        st.markdown("""
        このアプリは、キーワードからSEO最適化されたブログ記事を自動生成します。
        
        ### 使い方
        1. キーワードを入力
        2. タイトルを選択
        3. 記事を生成・編集
        
        ### 注意
        - Claude APIキーが必要です
        - 生成される記事は編集・確認が必要です
        """)
        
        st.divider()
        st.markdown("© 2025 SEOブログ記事生成アプリ")
    
    # メインコンテンツ
    st.title("SEOブログ記事生成アプリ")
    
    # セッション状態の初期化
    init_session_state()
    
    # 現在のステップに応じた画面表示
    if st.session_state.step == 1:
        show_keyword_input()
    elif st.session_state.step == 2:
        show_title_selection()
    elif st.session_state.step == 3:
        show_article_view()

if __name__ == "__main__":
    main()