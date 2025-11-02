# 定義一個 Python 支援的文字編碼清單
# Define a list of text encodings supported by Python

python_encodings_list = [
    'ascii',  # ASCII 編碼 (基本的英文字符集, 7-bit) / Basic English character set
    'big5',  # Big5 編碼 (繁體中文常用, 台灣/香港) / Traditional Chinese encoding (Taiwan/HK)
    'big5hkscs',  # Big5-HKSCS (香港增補字集) / Big5 with Hong Kong Supplementary Character Set
    'cp037',  # IBM EBCDIC US/Canada / IBM mainframe encoding
    'cp273',  # IBM EBCDIC Germany / 德國 EBCDIC 編碼
    'cp424',  # IBM EBCDIC Hebrew / 希伯來文編碼
    'cp437',  # 原始 IBM PC 編碼 (DOS Latin US) / Original IBM PC encoding
    'cp500',  # IBM EBCDIC International / 國際版 EBCDIC
    'cp720',  # 阿拉伯文 (DOS) / Arabic (DOS)
    'cp737',  # 希臘文 (DOS) / Greek (DOS)
    'cp775',  # 波羅的海語系 (DOS) / Baltic languages (DOS)
    'cp850',  # 西歐語系 (DOS) / Western Europe (DOS)
    'cp852',  # 中歐語系 (DOS) / Central Europe (DOS)
    'cp855',  # 西里爾字母 (DOS) / Cyrillic (DOS)
    'cp856',  # 希伯來文 (DOS) / Hebrew (DOS)
    'cp857',  # 土耳其文 (DOS) / Turkish (DOS)
    'cp858',  # 西歐語系 (含歐元符號) / Western Europe with Euro sign
    'cp860',  # 葡萄牙文 (DOS) / Portuguese (DOS)
    'cp861',  # 冰島文 (DOS) / Icelandic (DOS)
    'cp862',  # 希伯來文 (DOS) / Hebrew (DOS)
    'cp863',  # 加拿大法文 (DOS) / Canadian French (DOS)
    'cp864',  # 阿拉伯文 (DOS) / Arabic (DOS)
    'cp865',  # 北歐語系 (DOS) / Nordic languages (DOS)
    'cp866',  # 俄文 (DOS) / Russian (DOS)
    'cp869',  # 希臘文 (DOS) / Greek (DOS)
    'cp874',  # 泰文 (Windows) / Thai (Windows)
    'cp875',  # IBM EBCDIC Greek / 希臘文 EBCDIC
    'cp932',  # 日文 Shift_JIS (Windows) / Japanese Shift_JIS (Windows)
    'cp949',  # 韓文 (Windows) / Korean (Windows)
    'cp950',  # 繁體中文 Big5 (Windows) / Traditional Chinese Big5 (Windows)
    'cp1006',  # 烏爾都文 (Urdu) / Urdu
    'cp1026',  # IBM EBCDIC Turkish / 土耳其文 EBCDIC
    'cp1125',  # 烏克蘭文 (DOS) / Ukrainian (DOS)
    'cp1140',  # EBCDIC with Euro / EBCDIC 含歐元符號
    'cp1250',  # 中歐語系 (Windows) / Central Europe (Windows)
    'cp1251',  # 西里爾字母 (Windows) / Cyrillic (Windows)
    'cp1252',  # 西歐語系 (Windows, 常見) / Western Europe (Windows, very common)
    'cp1253',  # 希臘文 (Windows) / Greek (Windows)
    'cp1254',  # 土耳其文 (Windows) / Turkish (Windows)
    'cp1255',  # 希伯來文 (Windows) / Hebrew (Windows)
    'cp1256',  # 阿拉伯文 (Windows) / Arabic (Windows)
    'cp1257',  # 波羅的海語系 (Windows) / Baltic (Windows)
    'cp1258',  # 越南文 (Windows) / Vietnamese (Windows)
    'euc_jp',  # 日文 EUC 編碼 / Japanese EUC encoding
    'euc_jis_2004',  # 日文 EUC (JIS 2004) / Japanese EUC (JIS 2004)
    'euc_jisx0213',  # 日文 EUC (JIS X 0213) / Japanese EUC (JIS X 0213)
    'euc_kr',  # 韓文 EUC 編碼 / Korean EUC encoding
    'gb2312',  # 簡體中文 (舊標準) / Simplified Chinese (older standard)
    'gbk',  # 簡體中文 (擴展) / Simplified Chinese (extended)
    'gb18030',  # 簡體中文 (最新國標) / Simplified Chinese (latest national standard)
    'hz',  # HZ-GB-2312 (簡體中文, 郵件常用) / Simplified Chinese (email encoding)
    'iso2022_jp',  # 日文 ISO-2022-JP / Japanese ISO-2022-JP
    'iso2022_jp_1',  # 日文 ISO-2022-JP-1 / Japanese ISO-2022-JP-1
    'iso2022_jp_2',  # 日文 ISO-2022-JP-2 / Japanese ISO-2022-JP-2
    'iso2022_jp_2004',  # 日文 ISO-2022-JP-2004 / Japanese ISO-2022-JP-2004
    'iso2022_jp_3',  # 日文 ISO-2022-JP-3 / Japanese ISO-2022-JP-3
    'iso2022_jp_ext',  # 日文 ISO-2022-JP-EXT / Japanese ISO-2022-JP-EXT
    'iso2022_kr',  # 韓文 ISO-2022-KR / Korean ISO-2022-KR
    'latin_1',  # ISO-8859-1 (西歐語系, 常見) / Western Europe (very common)
    'iso8859_2',  # 中歐語系 / Central Europe
    'iso8859_3',  # 南歐語系 / South Europe
    'iso8859_4',  # 北歐語系 / North Europe
    'iso8859_5',  # 西里爾字母 / Cyrillic
    'iso8859_6',  # 阿拉伯文 / Arabic
    'iso8859_7',  # 希臘文 / Greek
    'iso8859_8',  # 希伯來文 / Hebrew
    'iso8859_9',  # 土耳其文 / Turkish
    'iso8859_10',  # 北歐語系 / Nordic
    'iso8859_11',  # 泰文 / Thai
    'iso8859_13',  # 波羅的海語系 / Baltic
    'iso8859_14',  # 凱爾特語 / Celtic
    'iso8859_15',  # 西歐語系 (含歐元) / Western Europe with Euro
    'iso8859_16',  # 東歐語系 / Eastern Europe
    'johab',  # 韓文 Johab 編碼 / Korean Johab encoding
    'koi8_r',  # 俄文 KOI8-R / Russian KOI8-R
    'koi8_t',  # 塔吉克文 KOI8-T / Tajik KOI8-T
    'koi8_u',  # 烏克蘭文 KOI8-U / Ukrainian KOI8-U
    'kz1048',  # 哈薩克文 / Kazakh
    'mac_cyrillic',  # Mac OS 西里爾字母 / Mac Cyrillic
    'mac_greek',  # Mac OS 希臘文 / Mac Greek
    'mac_iceland',  # Mac OS 冰島文 / Mac Icelandic
    'mac_latin2',  # Mac OS 中歐語系 / Mac Central Europe
    'mac_roman',  # Mac OS 西歐語系 / Mac Roman
    'mac_turkish',  # Mac OS 土耳其文 / Mac Turkish
    'ptcp154',  # 中亞語系 (西里爾字母) / Central Asian Cyrillic
    'shift_jis',  # 日文 Shift JIS 編碼 (常見於 Windows 與網頁) / Japanese Shift JIS encoding (commonly used in Windows & web)
    'shift_jis_2004',  # 日文 Shift JIS (JIS 2004 標準) / Japanese Shift JIS (JIS 2004 standard)
    'shift_jisx0213',  # 日文 Shift JIS (JIS X 0213 擴展) / Japanese Shift JIS (JIS X 0213 extension)
    'utf_32',  # UTF-32 (依平台大小端序, 4 bytes per char) / UTF-32 (platform-dependent endianness, 4 bytes per char)
    'utf_32_be',  # UTF-32 Big Endian / UTF-32 大端序
    'utf_32_le',  # UTF-32 Little Endian / UTF-32 小端序
    'utf_16',  # UTF-16 (依平台大小端序, 2 or 4 bytes per char) / UTF-16 (platform-dependent endianness)
    'utf_16_be',  # UTF-16 Big Endian / UTF-16 大端序
    'utf_16_le',  # UTF-16 Little Endian / UTF-16 小端序
    'utf_7',  # UTF-7 (為電子郵件設計, 已過時) / UTF-7 (designed for email, obsolete)
    'utf_8',  # UTF-8 (最常用, 網頁與跨平台標準) / UTF-8 (most common, web & cross-platform standard)
    'utf_8_sig'  # UTF-8 with BOM (Byte Order Mark) / UTF-8 含 BOM 標記
]
