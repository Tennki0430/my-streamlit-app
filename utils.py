"""
SEOブログ記事生成アプリのユーティリティモジュール
"""
import re
import json
import pyperclip
import anthropic
import markdown
from typing import List, Dict, Any, Optional

class ClaudeClient:
    """
    Claude APIとの通信を担当するクラス
    """
    def __init__(self, api_key: str):
        """
        初期化
        
        Args:
            api_key (str): Anthropic Claude API キー
        """
from anthropic import Client

class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = Client(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"

    
    def generate_titles(self, main_keyword: str, related_keywords: List[str], target_audience: str) -> List[str]:
        """
        キーワードに基づいてタイトル候補を生成
        
        Args:
            main_keyword (str): メインキーワード
            related_keywords (List[str]): 関連キーワードのリスト
            target_audience (str): ターゲット読者層
            
        Returns:
            List[str]: 生成されたタイトルのリスト
        """
        # プロンプトの構築
        prompt = f"""
メインキーワード「{main_keyword}」に関するSEO最適化されたブログ記事のタイトル候補を5つ生成してください。

関連キーワード: {', '.join(related_keywords) if related_keywords else 'なし'}
ターゲット読者層: {target_audience}

条件:
- クリック率を高める魅力的なタイトル
- メインキーワードを含む
- 30文字以内が望ましい
- 検索意図に合致する
- 数字を含めると効果的

以下のJSON形式で出力してください:
```json
{{
  "titles": [
    "タイトル1",
    "タイトル2",
    "タイトル3",
    "タイトル4",
    "タイトル5"
  ]
}}
```
JSON形式以外の説明は不要です。
"""
        
        try:
            # Claude APIを呼び出し
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # レスポンスからJSONを抽出
            content = response.content[0].text
            json_match = re.search(r'```json\s*(.*?)```', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                return result.get("titles", [])
            else:
                # JSON形式でない場合は直接パース
                try:
                    result = json.loads(content)
                    return result.get("titles", [])
                except:
                    # テキスト処理のフォールバック
                    titles = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('{') and not line.startswith('}'):
                            clean_line = line.strip('"').strip("'").strip(',')
                            if clean_line:
                                titles.append(clean_line)
                    return titles[:5]  # 最大5つのタイトルを返す
        except Exception as e:
            print(f"タイトル生成中にエラーが発生しました: {str(e)}")
            return []
    
    def evaluate_seo_title(self, title: str, main_keyword: str) -> Dict[str, Any]:
        """
        タイトルのSEO評価を行う
        
        Args:
            title (str): 評価するタイトル
            main_keyword (str): メインキーワード
            
        Returns:
            Dict[str, Any]: スコアとコメントを含む辞書
        """
        # 評価基準
        score = 100
        comments = []
        
        # キーワードを含むか
        if main_keyword.lower() not in title.lower():
            score -= 30
            comments.append("メインキーワードが含まれていません")
        
        # タイトルの長さ
        title_length = len(title)
        if title_length > 35:
            score -= 15
            comments.append("タイトルが長すぎます（30文字以下が望ましい）")
        elif title_length < 10:
            score -= 10
            comments.append("タイトルが短すぎます")
        
        # 数字を含むか
        if not any(c.isdigit() for c in title):
            score -= 5
            comments.append("数字を含めるとCTRが向上する可能性があります")
        
        # 魅力的な表現
        click_bait_words = ["方法", "コツ", "秘訣", "完全", "ガイド", "最高", "効果", "おすすめ", "人気", "必須"]
        if not any(word in title for word in click_bait_words):
            score -= 5
            comments.append("魅力的な表現を追加するとよいでしょう")
        
        # 最終スコアの調整
        score = max(0, min(100, score))
        
        # コメントのまとめ
        if score >= 80:
            summary = "優れたSEOタイトルです" if not comments else "良いタイトルですが、改善の余地があります"
        elif score >= 60:
            summary = "平均的なSEOタイトルです。改善点があります"
        else:
            summary = "SEO観点から改善が必要です"
        
        if comments:
            comment = f"{summary}: {' / '.join(comments)}"
        else:
            comment = summary
        
        return {
            "score": score,
            "comment": comment
        }
    
    def generate_article(self, title: str, main_keyword: str, related_keywords: List[str], 
                          target_audience: str, length: str) -> str:
        """
        ブログ記事を生成
        
        Args:
            title (str): 記事のタイトル
            main_keyword (str): メインキーワード
            related_keywords (List[str]): 関連キーワードのリスト
            target_audience (str): ターゲット読者層
            length (str): 記事の長さ（短め、標準、長め）
            
        Returns:
            str: 生成された記事（マークダウン形式）
        """
        # 記事の長さに応じたトークン数
        length_tokens = {
            "短め": 1500,
            "標準": 2500,
            "長め": 3500
        }
        
        max_tokens = length_tokens.get(length, 2500)
        
        # 関連キーワードの文字列化
        related_keywords_str = ', '.join(related_keywords) if related_keywords else 'なし'
        
        # プロンプトの構築
        prompt = f"""
以下の情報に基づいてSEO最適化されたブログ記事を日本語で作成してください。

タイトル: {title}
メインキーワード: {main_keyword}
関連キーワード: {related_keywords_str}
ターゲット読者層: {target_audience}
記事の長さ: {length}

SEO対策のガイドライン:
1. メインキーワードをタイトル、導入部、各セクションの見出し、結論に含める
2. 関連キーワードを自然に文中に散りばめる
3. 適切な見出し構造（H1、H2、H3）を使用する
4. 読みやすい短い段落で構成する
5. 箇条書きリストを効果的に使用する
6. 読者の関心を引く導入部と行動を促す結論を書く

記事は以下のマークダウン形式で作成してください:
1. H1見出しはタイトルのみ（# タイトル）
2. メインセクションはH2見出し（## 見出し）
3. サブセクションはH3見出し（### 見出し）
4. 箇条書きリストは適宜使用（- 項目）
5. 強調したい部分は太字（**強調**）

マークダウン形式の記事のみを出力してください。追加の説明や前置きは不要です。
"""
        
        try:
            # Claude APIを呼び出し
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # レスポンスから記事を抽出
            article = response.content[0].text
            
            # マークダウンフォーマットの調整
            article = article.strip()
            
            # コードブロックが含まれている場合はそれを削除
            if article.startswith("```markdown") and article.endswith("```"):
                article = article[10:-3].strip()
            elif article.startswith("```") and article.endswith("```"):
                article = article[3:-3].strip()
                
            return article
            
        except Exception as e:
            print(f"記事生成中にエラーが発生しました: {str(e)}")
            return ""


class SEOAnalyzer:
    """
    SEO分析を行うクラス
    """
    def analyze_keyword_density(self, text: str, keyword: str) -> Dict[str, Any]:
        """
        キーワード密度を分析
        
        Args:
            text (str): 分析するテキスト
            keyword (str): 分析するキーワード
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        # マークダウン記法を削除してテキストのみを抽出
        clean_text = re.sub(r'#|\*|_|-|\[|\]|\(|\)|`', '', text)
        
        # 単語数をカウント
        words = re.findall(r'\w+', clean_text)
        total_words = len(words)
        
        # キーワードの出現回数
        keyword_count = 0
        keyword_lower = keyword.lower()
        
        # テキスト内でキーワードを検索
        text_lower = clean_text.lower()
        keyword_count = text_lower.count(keyword_lower)
        
        # キーワード密度の計算
        density = (keyword_count / total_words * 100) if total_words > 0 else 0
        
        # 推奨事項
        if density < 0.5:
            recommendation = "キーワード密度が低すぎます。記事内でキーワードをもう少し使用することを検討してください。"
        elif density > 3.0:
            recommendation = "キーワード密度が高すぎる可能性があります。自然な文章になるよう調整してください。"
        else:
            recommendation = "キーワード密度は適切な範囲内です。"
        
        return {
            "keyword_count": keyword_count,
            "total_words": total_words,
            "density": round(density, 2),
            "recommendation": recommendation
        }
    
    def analyze_headings(self, text: str) -> Dict[str, Any]:
        """
        見出し構造を分析
        
        Args:
            text (str): 分析するテキスト
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        # 見出しのカウント
        h1_count = len(re.findall(r'^# ', text, re.MULTILINE))
        h2_count = len(re.findall(r'^## ', text, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', text, re.MULTILINE))
        h4_count = len(re.findall(r'^#### ', text, re.MULTILINE))
        h5_count = len(re.findall(r'^##### ', text, re.MULTILINE))
        h6_count = len(re.findall(r'^###### ', text, re.MULTILINE))
        
        # 見出し構造の評価
        has_h1 = h1_count > 0
        has_h2 = h2_count > 0
        too_many_h1 = h1_count > 1
        
        # 良い見出し構造かどうかの判定
        is_good_structure = has_h1 and has_h2 and not too_many_h1
        
        return {
            "counts": {
                "h1": h1_count,
                "h2": h2_count,
                "h3": h3_count,
                "h4": h4_count,
                "h5": h5_count,
                "h6": h6_count
            },
            "has_h1": has_h1,
            "has_h2": has_h2,
            "too_many_h1": too_many_h1,
            "is_good_structure": is_good_structure
        }
    
    def analyze_readability(self, text: str) -> Dict[str, Any]:
        """
        文章の読みやすさを分析
        
        Args:
            text (str): 分析するテキスト
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        # マークダウン記法を削除してテキストのみを抽出
        clean_text = re.sub(r'#|\*|_|-|\[|\]|\(|\)|`', '', text)
        
        # 段落の分割
        paragraphs = re.split(r'\n\s*\n', clean_text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        paragraph_count = len(paragraphs)
        
        # 文の分割（日本語の場合は句点で区切る）
        sentences = re.split(r'[。.!?！？]+', clean_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        # 長い段落のカウント（100文字以上を「長い」とする）
        long_paragraphs_count = sum(1 for p in paragraphs if len(p) > 100)
        
        # 平均段落長と平均文長の計算
        avg_paragraph_length = sum(len(p) for p in paragraphs) / paragraph_count if paragraph_count > 0 else 0
        avg_sentence_length = sum(len(s) for s in sentences) / sentence_count if sentence_count > 0 else 0
        
        # 読みやすさの評価
        is_good_readability = (avg_paragraph_length < 120 and 
                              avg_sentence_length < 50 and 
                              long_paragraphs_count / paragraph_count < 0.3 if paragraph_count > 0 else True)
        
        return {
            "paragraph_count": paragraph_count,
            "sentence_count": sentence_count,
            "long_paragraphs_count": long_paragraphs_count,
            "avg_paragraph_length": avg_paragraph_length,
            "avg_sentence_length": avg_sentence_length,
            "is_good_readability": is_good_readability
        }


class MarkdownProcessor:
    """
    マークダウンの処理を行うクラス
    """
    def convert_to_html(self, markdown_text: str) -> str:
        """
        マークダウンをHTMLに変換
        
        Args:
            markdown_text (str): マークダウンテキスト
            
        Returns:
            str: 変換されたHTML
        """
        try:
            # マークダウンをHTMLに変換
            html = markdown.markdown(
                markdown_text,
                extensions=['extra', 'nl2br', 'sane_lists']
            )
            
            # 基本的なスタイルを適用
            styled_html = f"""
            <style>
                .markdown-body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #24292e;
                    max-width: 100%;
                    padding: 20px;
                }}
                .markdown-body h1 {{
                    font-size: 2em;
                    margin-bottom: 0.5em;
                    border-bottom: 1px solid #eaecef;
                    padding-bottom: 0.3em;
                }}
                .markdown-body h2 {{
                    font-size: 1.5em;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                    border-bottom: 1px solid #eaecef;
                    padding-bottom: 0.3em;
                }}
                .markdown-body h3 {{
                    font-size: 1.25em;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }}
                .markdown-body p {{
                    margin-bottom: 1em;
                }}
                .markdown-body ul, .markdown-body ol {{
                    margin-bottom: 1em;
                    padding-left: 2em;
                }}
                .markdown-body li {{
                    margin-bottom: 0.25em;
                }}
                .markdown-body strong {{
                    font-weight: 600;
                }}
                .markdown-body a {{
                    color: #0366d6;
                    text-decoration: none;
                }}
                .markdown-body a:hover {{
                    text-decoration: underline;
                }}
            </style>
            <div class="markdown-body">
                {html}
            </div>
            """
            
            return styled_html
        except Exception as e:
            print(f"HTML変換エラー: {str(e)}")
            return f"<div>変換エラー: {str(e)}</div>"
    
    def add_toc_if_needed(self, markdown_text: str) -> str:
        """
        マークダウンに目次を追加（既に目次がある場合は追加しない）
        
        Args:
            markdown_text (str): マークダウンテキスト
            
        Returns:
            str: 目次が追加されたマークダウン
        """
        # 既に目次がある場合は何もしない
        if "## 目次" in markdown_text or "##目次" in markdown_text:
            return markdown_text
        
        # 見出しを抽出
        headings = []
        for line in markdown_text.split('\n'):
            match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                
                # H1は目次には含めない（タイトルのため）
                if level > 1:
                    headings.append((level, text))
        
        # 見出しがない場合は何もしない
        if not headings:
            return markdown_text
        
        # 目次を生成
        toc = ["## 目次", ""]
        for level, text in headings:
            indent = "  " * (level - 2)  # H2は基本レベル
            link_text = text.replace('[', '').replace(']', '')  # リンクテキストからマークダウン記号を削除
            anchor = link_text.lower().replace(' ', '-')  # アンカーリンク用のID
            toc.append(f"{indent}- [{link_text}](#{anchor})")
        
        toc.append("")  # 目次の後に空行
        
        # タイトル部分と本文部分を分離
        parts = markdown_text.split('\n\n', 1)
        
        if len(parts) > 1:
            title_part, body_part = parts
            return title_part + '\n\n' + '\n'.join(toc) + '\n\n' + body_part
        else:
            # タイトルだけの場合
            return markdown_text + '\n\n' + '\n'.join(toc)
    
    def save_to_clipboard(self, text: str) -> bool:
        """
        テキストをクリップボードにコピー
        
        Args:
            text (str): コピーするテキスト
            
        Returns:
            bool: 成功したかどうか
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"クリップボードへのコピーエラー: {str(e)}")
            return False
