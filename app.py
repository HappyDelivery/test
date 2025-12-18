import streamlit as st
import google.generativeai as genai
import time
import os

# ==========================================
# 1. 페이지 설정 및 디자인 (CSS)
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI V5",
    page_icon="🧬",
    layout="wide"
)

# 고급스러운 다크 테마 및 UI 스타일링
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #262730; color: #ffffff; 
        border: 1px solid #4b5563; border-radius: 8px;
    }
    
    /* 버튼 스타일 (그라데이션) */
    .stButton > button {
        background: linear-gradient(90deg, #4776E6 0%, #8E54E9 100%);
        color: white; border: none; font-weight: bold; height: 50px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(142, 84, 233, 0.4);
    }
    
    /* 결과창 박스 */
    .result-box {
        background-color: #1e1e1e; padding: 25px;
        border-radius: 10px; border: 1px solid #444;
        font-family: 'Courier New', monospace; line-height: 1.6;
    }
    
    /* 에러 메시지 스타일 */
    .error-box {
        background-color: #450a0a; color: #fca5a5; padding: 15px;
        border-radius: 8px; border: 1px solid #991b1b;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 확장된 템플릿 데이터 (20종 이상)
# ==========================================
TEMPLATES = {
    "✨ 직접 입력 (Custom)": {"persona": "", "task": "", "context": ""},
    
    # --- 마케팅 & 비즈니스 ---
    "📝 SEO 블로그 포스팅": {
        "persona": "SEO 마케팅 전문가 및 테크니컬 라이터",
        "task": "주어진 키워드를 자연스럽게 포함하여 검색 엔진 상위 노출을 노리는 정보성 블로그 글을 작성하라.",
        "context": "소제목(H2, H3)을 구조적으로 배치, 체류 시간 증대 유도"
    },
    "📧 콜드 메일 (영업 제안)": {
        "persona": "B2B 세일즈 카피라이터",
        "task": "수신자의 관심을 즉시 사로잡고 미팅으로 연결될 수 있는 매력적인 제안 메일을 작성하라.",
        "context": "스팸으로 분류되지 않도록 진정성 있는 톤 사용, 명확한 CTA 포함"
    },
    "📣 SNS 카드뉴스 기획": {
        "persona": "인스타그램 콘텐츠 기획자",
        "task": "사람들이 저장하고 공유하고 싶어지는 카드뉴스 10장 분량의 스토리보드를 기획하라.",
        "context": "첫 장은 강력한 후킹 멘트, 마지막 장은 팔로우 유도"
    },
    "🛍️ 상품 상세페이지 카피": {
        "persona": "이커머스 상세페이지 기획자",
        "task": "고객의 구매 욕구를 자극하는 상품 상세페이지 도입부와 특징 설명(USP)을 작성하라.",
        "context": "고객의 문제(Pain Point)를 지적하고 해결책 제시"
    },

    # --- 유튜브 & 크리에이터 ---
    "🎬 유튜브 영상 대본 (정보성)": {
        "persona": "100만 지식 유튜버 PD",
        "task": "시청 지속 시간을 극대화할 수 있는 8분 분량의 유튜브 영상 스크립트를 작성하라.",
        "context": "초반 30초 내에 강력한 훅(Hook) 배치, 쉽고 재미있는 설명"
    },
    "🎥 유튜브 숏츠 대본 (1분)": {
        "persona": "틱톡/숏츠 바이럴 전문가",
        "task": "1분 이내에 시청자의 도파민을 자극하는 빠른 템포의 숏폼 대본을 작성하라.",
        "context": "반전 요소 포함, 화면 전환 가이드 제시"
    },

    # --- 개발 & 데이터 ---
    "💻 파이썬 코드 생성": {
        "persona": "Google 수석 소프트웨어 엔지니어",
        "task": "요구사항을 충족하는 효율적이고 안전한 Python 코드를 작성하고, 각 줄에 주석을 달아라.",
        "context": "PEP8 스타일 준수, 에러 처리(Try-Except) 포함"
    },
    "🐞 코드 리뷰 및 리팩토링": {
        "persona": "엄격한 코드 리뷰어",
        "task": "제공된 코드의 잠재적 버그를 찾고, 성능과 가독성을 높이는 방향으로 리팩토링하라.",
        "context": "시간 복잡도(Big-O) 고려, 변수명 개선 제안"
    },
    "📊 엑셀/구글시트 공식": {
        "persona": "데이터 분석가",
        "task": "복잡한 데이터 처리를 자동화할 수 있는 엑셀 함수 식을 작성하고 사용법을 설명하라.",
        "context": "초보자도 이해하기 쉽게 단계별 설명"
    },

    # --- 글쓰기 & 학업 ---
    "📚 자기소개서/에세이": {
        "persona": "전문 커리어 컨설턴트",
        "task": "지원자의 경험을 바탕으로 직무 역량이 돋보이는 자기소개서 초안을 작성하라.",
        "context": "STAR 기법(상황-과제-행동-결과) 활용"
    },
    "🗣️ 영어 회화 롤플레잉": {
        "persona": "미국 원어민 회화 튜터",
        "task": "사용자와 특정 상황(공항, 식당, 비즈니스)에서 대화를 나누며 영어 표현을 교정하라.",
        "context": "틀린 표현은 부드럽게 수정하고 더 나은 표현 제안"
    }
}

# ==========================================
# 3. 사이드바: 설정 및 보안
# ==========================================
with st.sidebar:
    # 캐릭터 표시 (파일이 있으면)
    if os.path.exists("character.png"):
        st.image("character.png", width=200)
    else:
        st.write("🦸‍♂️") # 기본 이모지

    st.markdown("### 🔒 보안 및 설정")
    
    # [중요] API Key 입력창 비워두기 (보안 강화)
    # Streamlit Secrets를 사용하면 매번 입력 안 해도 됩니다.
    default_key = st.secrets.get("GOOGLE_API_KEY", "")
    
    api_key = st.text_input(
        "Google API Key",
        value=default_key,
        type="password",  # 비밀번호처럼 ••• 표시
        placeholder="AIza... 로 시작하는 키를 붙여넣으세요",
        help="이 키는 어디에도 저장되지 않고 휘발됩니다."
    )
    
    # 모델 선택 (Flash 모델을 기본값으로 추천)
    # Pro 모델은 429 에러가 자주 발생하므로 Flash를 맨 위에 둡니다.
    model_options = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    selected_model = st.selectbox(
        "AI 모델 선택 (추천: Flash)", 
        model_options,
        index=0, # Flash 기본 선택
        help="Flash 모델이 속도가 빠르고 무료 사용량이 넉넉합니다."
    )
    
    temperature = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)
    
    st.info("""
    **💡 Tip:** 'Quota Exceeded' 오류가 발생하면 
    모델을 **gemini-1.5-flash**로 변경하세요.
    """)
    st.markdown("---")
    st.caption("Developed by **20년차 개발자**")

# ==========================================
# 4. 메인 UI
# ==========================================
st.title("PromptGenesis AI V5")
st.markdown("##### 🚀 당신의 아이디어를 '최고의 프롬프트'로 바꿔주는 생성기")

# 2단 레이아웃
col_left, col_right = st.columns([1, 1], gap="large")

# --- [왼쪽] 입력 패널 ---
with col_left:
    st.subheader("🛠️ 설계도 작성")
    
    # 카테고리 선택
    selected_template_name = st.selectbox("📌 어떤 프롬프트를 만들까요?", list(TEMPLATES.keys()))
    template_data = TEMPLATES[selected_template_name]
    
    with st.container(border=True):
        persona = st.text_input("🎭 페르소나 (AI의 역할)", value=template_data["persona"])
        task = st.text_area("🎯 핵심 과제 (AI가 할 일)", value=template_data["task"], height=120)
        context = st.text_area("📂 추가 맥락 / 제약 조건", value=template_data.get("context", ""), height=100, placeholder="예: 분량은 A4 1장, 어조는 정중하게...")
    
    generate_btn = st.button("✨ 슈퍼 프롬프트 생성 (Generate)", type="primary", use_container_width=True)

# --- [오른쪽] 결과 패널 ---
with col_right:
    st.subheader("💎 생성된 프롬프트")
    
    output_area = st.empty()
    
    if generate_btn:
        if not api_key:
            st.warning("👈 왼쪽 사이드바에 **Google API Key**를 입력해주세요.")
        else:
            try:
                # 1. 로딩 애니메이션
                output_area.markdown("""
                    <div style="text-align: center; padding: 40px;">
                        <img src="https://i.gifer.com/ZZ5H.gif" width="60">
                        <p style="color: #888; margin-top: 10px;">최적의 프롬프트를 설계 중입니다...</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 2. 모델 연결
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                
                # 3. 메타 프롬프트 (프롬프트를 짜주는 프롬프트)
                meta_prompt = f"""
                당신은 세계 최고의 프롬프트 엔지니어입니다.
                아래 사용자의 요구사항을 바탕으로, ChatGPT나 Gemini 같은 LLM에게 입력했을 때 최상의 결과를 낼 수 있는 **'시스템 프롬프트'**를 작성해주세요.

                [사용자 입력 정보]
                - 역할: {persona}
                - 작업: {task}
                - 맥락: {context}

                [작성 가이드]
                1. 프롬프트는 그대로 복사해서 쓸 수 있도록 **마크다운 코드 블록** 안에 작성하세요.
                2. [Role], [Task], [Context], [Constraints], [Output Format] 등 구조화된 섹션으로 나누세요.
                3. 변수가 필요한 곳은 {{변수명}} 처리하세요.
                4. 언어는 한국어로 작성하되, 필요하다면 영어 지시문을 병기하세요.
                """
                
                # 4. API 요청
                response = model.generate_content(
                    meta_prompt,
                    generation_config={"temperature": temperature}
                )
                
                # 5. 결과 출력
                output_area.markdown(response.text)
                st.toast("✅ 프롬프트 생성 완료!", icon="🎉")
                
            except Exception as e:
                # 에러 핸들링 (Quota Exceeded 등)
                err_msg = str(e)
                if "429" in err_msg or "Quota" in err_msg:
                    st.error("🚨 **사용량 한도 초과 (429 Error)**")
                    st.markdown("""
                    <div class="error-box">
                        <b>원인:</b> 현재 선택한 모델의 무료 사용량을 초과했습니다.<br>
                        <b>해결책:</b> 사이드바에서 모델을 <b>'gemini-1.5-flash'</b>로 변경하고 다시 시도하세요.
                        이 모델은 속도가 빠르고 사용 제한이 훨씬 덜합니다.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"오류가 발생했습니다: {e}")
    else:
        # 대기 화면
        output_area.info("왼쪽에서 내용을 입력하고 버튼을 누르면, 여기에 전문가용 프롬프트가 나타납니다.")
