import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 페이지 설정 및 커스텀 디자인 (CSS)
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI V3",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 다크/네온 테마 CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 입력 필드 디자인 */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #262730; color: #ffffff; 
        border: 1px solid #4b5563; border-radius: 8px;
    }
    
    /* 버튼 그라데이션 */
    .stButton > button {
        background: linear-gradient(45deg, #2563eb, #9333ea);
        color: white; border: none; font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 10px rgba(147, 51, 234, 0.5);
    }
    
    /* 결과창 박스 */
    .result-box {
        background-color: #1e1e1e; padding: 20px;
        border-radius: 10px; border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터셋: 템플릿 및 옵션 확장
# ==========================================

# 15가지 이상의 다양한 활용 분야 템플릿
TEMPLATES = {
    "✨ 직접 입력 (Custom)": {"persona": "", "task": "", "tone": "전문적인"},
    "📝 블로그 글 (SEO 최적화)": {
        "persona": "SEO 전문 마케터 및 파워 블로거",
        "task": "주어진 주제로 검색 엔진 상위 노출을 노리는 블로그 글을 작성하세요. 소제목(H2, H3)을 구조적으로 사용하고, 독자가 머무르는 시간을 늘리기 위해 흥미로운 도입부를 작성하세요.",
        "tone": "친근하고 유익한"
    },
    "📧 비즈니스 콜드 메일": {
        "persona": "B2B 영업 전문가",
        "task": "잠재 고객에게 우리 서비스를 소개하고 미팅을 제안하는 콜드 메일을 작성하세요. 스팸처럼 보이지 않도록 개인화된 느낌을 주고, 명확한 Call to Action(CTA)을 포함하세요.",
        "tone": "정중하지만 설득력 있는"
    },
    "📊 엑셀/구글 시트 수식 생성": {
        "persona": "엑셀 및 데이터 분석 전문가",
        "task": "사용자가 원하는 데이터 처리를 위한 엑셀(구글 시트) 함수나 매크로를 작성하고, 각 인자에 대해 설명하세요.",
        "tone": "기술적이고 명확한"
    },
    "💻 파이썬 코드 생성 & 설명": {
        "persona": "Google 출신 시니어 소프트웨어 엔지니어",
        "task": "요구사항을 해결하는 효율적이고 Pythonic한 코드를 작성하세요. 코드에는 주석을 달고, 하단에 로직에 대한 설명을 덧붙이세요.",
        "tone": "전문적인 (Technical)"
    },
    "🎬 유튜브 스크립트 기획": {
        "persona": "100만 유튜버 PD",
        "task": "시청 지속 시간을 늘릴 수 있는 유튜브 영상 오프닝 멘트와 전체적인 대본 구성을 짜주세요. 훅(Hook)을 강력하게 넣으세요.",
        "tone": "재미있고 에너지가 넘치는"
    },
    "🎓 영어 회화 튜터": {
        "persona": "미국 원어민 영어 강사",
        "task": "사용자의 입력을 자연스러운 원어민 표현으로 교정해주고, 더 세련된 표현 3가지를 추천해주세요.",
        "tone": "친절하고 교육적인"
    },
    "📋 회의록 요약 및 할 일 정리": {
        "persona": "꼼꼼한 비즈니스 비서",
        "task": "중구난방인 회의 내용을 바탕으로 [핵심 안건], [결정 사항], [Action Item]으로 나누어 깔끔하게 요약하세요.",
        "tone": "객관적이고 간결한"
    },
    "🎨 인스타그램 캡션 & 해시태그": {
        "persona": "SNS 인플루언서",
        "task": "사진에 어울리는 감성적인 글귀와 유입을 늘릴 수 있는 관련 해시태그 15개를 추천해주세요.",
        "tone": "감성적이고 트렌디한"
    },
    "🍔 다이어트 식단 추천": {
        "persona": "전문 영양사 및 헬스 트레이너",
        "task": "사용자의 목표에 맞는 하루 식단표를 짜고, 칼로리와 영양소 균형을 설명하세요.",
        "tone": "동기부여가 되는"
    }
}

TONE_OPTIONS = [
    "전문적인 (Professional)", "친근한 (Friendly)", "설득력 있는 (Persuasive)", 
    "위트 있는 (Witty)", "간결한 (Concise)", "감성적인 (Emotional)", 
    "비판적인 (Critical)", "교육적인 (Educational)", "자신감 넘치는 (Confident)", "공손한 (Polite)"
]

FORMAT_OPTIONS = [
    "일반 텍스트", "마크다운(Markdown)", "표 (Table)", "HTML 코드", 
    "JSON 데이터", "이메일 형식", "코드 블록", "체크리스트"
]

# ==========================================
# 3. 사이드바 및 설정 (API & Model)
# ==========================================
with st.sidebar:
    st.header("⚙️ 환경 설정")
    
    # 1. API 키 입력 (기본값 설정됨)
    api_key = st.text_input("Google API Key", value="AIzaSyBVxYQzLTs8uRP4yyJYS8yBDewLSm896Jg", type="password")
    
    # 2. [핵심] 모델 자동 감지 로직
    available_models = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # API를 통해 사용 가능한 모델 목록을 가져옵니다.
            models = genai.list_models()
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    # gemini-1.5 가 포함된 모델만 필터링 (최신 모델 위주)
                    if 'gemini' in m.name:
                        available_models.append(m.name)
        except Exception:
            # API 키가 틀렸거나 네트워크 오류 시 기본값
            available_models = ["models/gemini-1.5-flash"]
    
    # 모델 선택 드롭다운 (이제 에러가 안 납니다!)
    # 모델 목록이 비어있을 경우 대비
    if not available_models:
        available_models = ["models/gemini-1.5-flash"]
        
    selected_model = st.selectbox("사용할 AI 모델", available_models, index=0)
    
    temperature = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7, help="높을수록 창의적, 낮을수록 정해진 답을 합니다.")
    
    st.divider()
    st.info(f"현재 선택된 모델:\n{selected_model}")

# ==========================================
# 4. 메인 UI (2단 레이아웃)
# ==========================================
st.title("🧬 PromptGenesis AI V3")
st.markdown("**당신의 아이디어를 실행 가능한 완벽한 결과물로 변환합니다.**")

col_left, col_right = st.columns([1, 1], gap="medium")

# --- 왼쪽: 입력 패널 ---
with col_left:
    st.subheader("🟦 프롬프트 설계")
    
    # 템플릿 선택
    cat_key = st.selectbox("🚀 활용 분야 선택 (자동 템플릿)", list(TEMPLATES.keys()))
    curr_tmpl = TEMPLATES[cat_key]

    # 입력 폼
    persona = st.text_input("🎭 페르소나 (역할)", value=curr_tmpl["persona"])
    task = st.text_area("🎯 핵심 과제 (지시사항)", value=curr_tmpl["task"], height=150)
    context = st.text_area("📂 배경 자료 / 데이터", placeholder="참고할 텍스트나 데이터를 여기에 붙여넣으세요...", height=100)
    
    c1, c2 = st.columns(2)
    with c1:
        # 출력 형식을 다중 선택이 아닌 단일 선택으로 변경 (명확성을 위해) 또는 콤보박스
        out_fmt = st.selectbox("📝 출력 형식", FORMAT_OPTIONS)
    with c2:
        # 톤 선택 (기본값 매칭)
        # 템플릿의 톤이 옵션에 있으면 그걸 선택, 아니면 첫 번째
        default_tone_idx = 0
        for i, t in enumerate(TONE_OPTIONS):
            if curr_tmpl["tone"] in t:
                default_tone_idx = i
                break
        tone = st.selectbox("🗣️ 어조 (Tone)", TONE_OPTIONS, index=default_tone_idx)

    generate_btn = st.button("✨ 결과 생성 (Generate)", type="primary")

# --- 오른쪽: 결과 패널 ---
with col_right:
    st.subheader("🟩 결과 확인")
    result_placeholder = st.empty() # 결과를 스트리밍으로 보여줄 공간

    if generate_btn:
        if not api_key:
            st.error("⚠️ API Key가 필요합니다.")
        else:
            try:
                # 모델 설정
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                
                # 프롬프트 조합
                full_prompt = f"""
                당신은 {persona}입니다. 아래 지시사항을 완벽하게 수행하세요.
                
                [Task]: {task}
                [Context]: {context}
                [Tone]: {tone}
                [Output Format]: {out_fmt}
                
                반드시 위 [Output Format]에 맞춰서 답변을 작성하세요.
                """
                
                # 스트리밍 요청 (타자 치는 효과)
                response = model.generate_content(
                    full_prompt,
                    stream=True, # 여기가 핵심!
                    generation_config={"temperature": temperature}
                )
                
                # 스트리밍 출력 로직
                full_text = ""
                for chunk in response:
                    if chunk.text:
                        full_text += chunk.text
                        # 마크다운 렌더링을 실시간으로
                        result_placeholder.markdown(f"""
                        <div class="result-box">
                            {full_text} ▌
                        </div>
                        """, unsafe_allow_html=True)
                
                # 완료 후 커서 제거 및 최종 출력
                result_placeholder.markdown(f"""
                <div class="result-box">
                    {full_text}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ 에러 발생: {e}")
                st.warning("API Key가 올바른지, 혹은 모델이 지원되는지 확인해주세요.")

    else:
        # 대기 화면
        result_placeholder.markdown("""
        <div style='text-align: center; color: #6b7280; padding: 100px 0; border: 2px dashed #374151; border-radius: 10px;'>
            <div style='font-size: 3rem;'>✨</div>
            <h3>준비 완료</h3>
            <p>왼쪽에서 설정을 마치고 생성 버튼을 눌러주세요.</p>
        </div>
        """, unsafe_allow_html=True)
