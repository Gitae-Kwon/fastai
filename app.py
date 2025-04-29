# app.py ───────────────────────────────────────────────────────────────
import streamlit as st, pandas as pd, re, io, pathlib
import openpyxl, xlsxwriter

# ── (고정) ③번 파일 경로 ─────────────────────────────────────────────
DATA_DIR     = pathlib.Path(__file__).parent / "data"
FILE3_A_PATH = DATA_DIR / "all_contents_A.xlsx"    # ★ A 모드용
FILE3_B_PATH = DATA_DIR / "all_contents_B.xlsx"    # ★ B 모드용

# ── 후보 컬럼 ─────────────────────────────────────────────────────────
FILE1_COL_CAND = ["콘텐츠명", "콘텐츠 제목", "Title", "ContentName", "제목"]
FILE2_COL_CAND = [
    "컨텐츠", "타이틀", "작품명", "도서명", "작품 제목",
    "상품명", "이용상품명", "상품 제목", "ProductName", "Title", "제목"
]
FILE3_COL_CAND = ["콘텐츠명", "콘텐츠 제목", "Title", "ContentName", "제목"]
FILE3_ID_CAND  = ["판매채널콘텐츠ID", "콘텐츠ID", "ID", "ContentID"]

# ── 유틸 ──────────────────────────────────────────────────────────────
def pick(cands, df):
    for c in cands:
        if c in df.columns:
            return c
    raise ValueError(f"가능한 컬럼이 없습니다 ➜ {cands}")

def clean_title(txt: str) -> str:
    t = str(txt)
    t = re.sub(r"\s*제\s*\d+[권화]", "", t)
    for k, v in {
        "Un-holyNight": "UnholyNight", "?": "", "~": "", ",": "", "-": "", "_": ""
    }.items():
        t = t.replace(k, v)
    t = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", t)
    t = re.sub(r"\d+[권화부회]", "", t)
    for kw in [
        "개정판 l", "개정판", "외전", "무삭제본", "무삭제판", "합본",
        "단행본", "시즌", "세트", "연재", "특별", "최종화", "완결",
        "2부", "무삭제", "완전판", "세개정판", "19세개정판"
    ]:
        t = t.replace(kw, "")
    t = re.sub(r"\d+", "", t).rstrip(".")
    t = re.sub(r"[\.~\-–—!@#$%^&*_=+\\|/:;\"'’`<>?，｡､{}()]", "", t)
    t = re.sub(r"특별$", "", t)
    return t.replace(" ", "").strip()

# ── UI ────────────────────────────────────────────────────────────────
st.title("📁 판매채널 및 콘텐츠마스터ID 매핑")

f1 = st.file_uploader(
    "① S2-판매채널 콘텐츠리스트\n"
    "(https://kiss.kld.kr/mst/sch/schn-ctns-search) 에서 채널 검색 후 다운로드\n"
    "※ 다운로드 후 ‘열기’ → ‘다른 이름으로 저장’하여 업로드해 주세요.",
    type="xlsx",
)
f2 = st.file_uploader("② 플랫폼별 정산서 (판매채널에서 제공한 정산서)", type="xlsx")

# ★ ③번 파일 모드 선택 -------------------------------------------------
mode = st.radio(
    "③ 사용할 S2 콘텐츠 전체 파일을 고르세요",
    ("A: all_contents_A.xlsx", "B: all_contents_B.xlsx"),
    index=0
)
st.caption(f"→ data 폴더의 **{FILE3_A_PATH.name if mode.startswith('A') else FILE3_B_PATH.name}** 를 사용합니다.")

save_name = st.text_input("💾 저장 파일명(확장자 제외)", value="mapping_result") + ".xlsx"

# ── 실행 --------------------------------------------------------------
if st.button("🟢 매핑 실행"):

    # 1) 입력 확인 ------------------------------------------------------
    if not (f1 and f2):
        st.error("file1, file2 두 개를 먼저 업로드해 주세요.")
        st.stop()

    # 2) ③번 파일 경로 결정 & 존재 체크 ★
    file3_path = FILE3_A_PATH if mode.startswith("A") else FILE3_B_PATH
    if not file3_path.exists():
        st.error(f"⚠️ {file3_path.name} 이 data 폴더에 없습니다.")
        st.stop()

    # 3) Excel → DataFrame --------------------------------------------
    df1 = pd.read_excel(f1)
    df2 = pd.concat(pd.read_excel(f2, sheet_name=None).values(), ignore_index=True)
    df3 = pd.read_excel(file3_path)

    # 4) 컬럼 자동 선택 -----------------------------------------------
    c1  = pick(FILE1_COL_CAND, df1)
    c2  = pick(FILE2_COL_CAND, df2)
    c3  = pick(FILE3_COL_CAND, df3)
    id3 = pick(FILE3_ID_CAND,  df3)

    # 5) 제목 정제 -----------------------------------------------------
    df1["정제_콘텐츠명"]  = df1[c1].apply(clean_title)
    df2["정제_상품명"]    = df2[c2].apply(clean_title)
    df3["정제_콘텐츠3명"] = df3[c3].apply(clean_title)

    # 6) 1차 매핑 -----------------------------------------------------
    map1 = (
        df1.drop_duplicates("정제_콘텐츠명")
           .set_index("정제_콘텐츠명")["판매채널콘텐츠ID"]
    )
    df2["매핑결과"] = df2["정제_상품명"].map(map1).fillna(df2["정제_상품명"])

    # 7) 2차 매핑 -----------------------------------------------------
    map3 = (
        df3.drop_duplicates("정제_콘텐츠3명")
           .set_index("정제_콘텐츠3명")[id3]
    )
    df2["최종_매핑결과"] = df2["정제_상품명"].map(map3).fillna(df2["매핑결과"])

    # 8) 매핑콘텐츠명 / 콘텐츠ID 생성 (기존 로직 유지) ------------------
    mask_pair  = df2["정제_상품명"] == df2["매핑결과"]
    base_pairs = (
        df2.loc[mask_pair, ["정제_상품명", "최종_매핑결과"]]
           .query("`정제_상품명`.str.strip() != ''", engine="python")
           .drop_duplicates()
           .rename(columns={"정제_상품명": "매핑콘텐츠명",
                            "최종_매핑결과": "콘텐츠ID"})
    )
    base_pairs["매핑콘텐츠명"] = base_pairs["매핑콘텐츠명"].apply(clean_title)

    dup_mask     = base_pairs["매핑콘텐츠명"] == base_pairs["콘텐츠ID"]
    pairs_unique = base_pairs.loc[~dup_mask].reset_index(drop=True)
    pairs_same   = base_pairs.loc[ dup_mask].reset_index(drop=True)

    pad_u = len(df2) - len(pairs_unique)
    df2["매핑콘텐츠명"] = list(pairs_unique["매핑콘텐츠명"]) + [""] * pad_u
    df2["콘텐츠ID"]     = list(pairs_unique["콘텐츠ID"])     + [""] * pad_u

    pad_s = len(df2) - len(pairs_same)
    df2["동일_매핑콘텐츠명"] = list(pairs_same["매핑콘텐츠명"]) + [""] * pad_s
    df2["동일_콘텐츠ID"]     = list(pairs_same["콘텐츠ID"])     + [""] * pad_s

    # 9) 최종 미매핑 & 정렬 (기존 로직 유지) ----------------------------
    used_titles   = set(base_pairs["매핑콘텐츠명"])
    final_unmatch = (
        df2.loc[mask_pair, "정제_상품명"]
           .drop_duplicates()
           .pipe(lambda s: s[~s.isin(map3.index)])
           .pipe(lambda s: s[~s.isin(used_titles)])
    )

    df2["최종_정렬된_매핑되지않은_상품명"] = (
        sorted(final_unmatch) + [""] * (len(df2) - len(final_unmatch))
    )
    df2["최종_매핑되지않은_상품명"] = df2["정제_상품명"].where(
        df2["정제_상품명"].isin(final_unmatch), ""
    )

    # 10) file1 정보 결합 & 컬럼 재배치, 숨김, 색상 등 모두 기존 코드 그대로 …
    #    (생략)

    st.success("✅ 매핑 완료! 아래 버튼으로 다운로드하세요.")
    st.download_button(
        "📥 결과 엑셀 다운로드",
        buf.getvalue(),
        file_name=save_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
