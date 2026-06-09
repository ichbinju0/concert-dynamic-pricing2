const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, Header, Footer, PageBreak,
} = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const headerBorder = { style: BorderStyle.SINGLE, size: 1, color: "1F3864" };
const headerBorders = { top: headerBorder, bottom: headerBorder, left: headerBorder, right: headerBorder };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, size: 32, font: "맑은 고딕", color: "1F3864" })],
    spacing: { before: 400, after: 200 },
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, size: 26, font: "맑은 고딕", color: "2E75B6" })],
    spacing: { before: 280, after: 120 },
  });
}

function body(text, { bold = false, indent = 0 } = {}) {
  return new Paragraph({
    children: [new TextRun({ text, bold, size: 22, font: "맑은 고딕" })],
    spacing: { before: 60, after: 60 },
    indent: indent ? { left: indent } : undefined,
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, size: 22, font: "맑은 고딕" })],
    spacing: { before: 40, after: 40 },
  });
}

function formula(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, size: 24, font: "Cambria Math", color: "1F3864", bold: true })],
    spacing: { before: 120, after: 120 },
    shading: { fill: "EBF3FB", type: ShadingType.CLEAR },
    indent: { left: 720, right: 720 },
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function makeTable(headers, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      borders: headerBorders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: "1F3864", type: ShadingType.CLEAR },
      margins: { top: 100, bottom: 100, left: 150, right: 150 },
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, bold: true, size: 20, font: "맑은 고딕", color: "FFFFFF" })],
      })],
    })),
  });
  const dataRows = rows.map((row, ri) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: ri % 2 === 0 ? "F5F9FF" : "FFFFFF", type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 150, right: 150 },
      children: [new Paragraph({
        children: [new TextRun({ text: cell, size: 20, font: "맑은 고딕" })],
      })],
    })),
  }));
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 문서 내용
// ─────────────────────────────────────────────────────────────────────────────
const children = [
  // 표지
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 1440, after: 400 },
    children: [new TextRun({ text: "IE209 팀 프로젝트 발표", bold: true, size: 48, font: "맑은 고딕", color: "1F3864" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "K-pop 콘서트 동적 가격 책정 AI 에이전트", bold: true, size: 36, font: "맑은 고딕", color: "2E75B6" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 1440 },
    children: [new TextRun({ text: "Dynamic Pricing AI Agent for K-pop Concerts", size: 26, font: "맑은 고딕", color: "595959" })],
  }),
  pageBreak(),

  // ── 1. 문제 및 가치 ──
  h1("1. 문제 정의 및 사회적 가치"),
  h2("1-1. 문제 배경"),
  body("K-pop 콘서트 티켓 시장은 구조적인 가격 비효율 문제를 안고 있습니다. 주최사는 수개월 전 단일 고정가를 책정하지만, 실제 소비자의 지불의향(WTP, Willingness-To-Pay)은 공연일까지 남은 기간(D-day), 아티스트 인기, 좌석 위치에 따라 크게 달라집니다."),
  body("이 가격 경직성이 초래하는 두 가지 비효율:"),
  bullet("수익 손실: 팬들이 기꺼이 더 높은 가격을 지불할 의향이 있음에도 주최사는 그 잉여를 회수하지 못합니다."),
  bullet("암시장 번성: 공식가와 시장가의 갭이 커질수록 티켓베이 등 재판매 플랫폼에서 수익이 중간자에게 귀속됩니다."),
  body(""),
  h2("1-2. 해결 방안 및 가치 제안"),
  body("본 프로젝트는 D-day·인기도·좌석 등급을 실시간으로 반영하는 AI 기반 동적 가격 책정 에이전트를 구축하여, 주최사 수익 극대화와 소비자 후생 개선을 동시에 달성합니다."),
  body(""),
  makeTable(
    ["이해관계자", "기존 문제", "본 시스템 가치"],
    [
      ["공연 주최사", "고정가 → 수익 기회 손실", "Joint LP 최적화로 수익 극대화"],
      ["팬/소비자", "암시장 웃돈 지불 강요", "정책적 가격 투명성 확보"],
      ["플랫폼/정부", "재판매 규제 어려움", "공정가격 데이터 기반 정책 지원"],
    ],
    [2500, 3000, 3860]
  ),
  body(""),

  pageBreak(),

  // ── 2. 데이터 수집 및 전처리 ──
  h1("2. 데이터 수집 및 전처리"),
  h2("2-1. 데이터 소스"),
  body("실제 티켓베이(Ticketbay) 재판매 크롤링 데이터를 수집하였으며, 4개 아티스트 콘서트 데이터를 확보하였습니다."),
  body(""),
  makeTable(
    ["아티스트", "인기도 점수", "데이터 규모", "비고"],
    [
      ["양요섭", "5", "다수 리스팅", "Solo 가수"],
      ["도겸 x 승관", "7", "다수 리스팅", "SEVENTEEN 멤버 (1,616만 팔로워)"],
      ["라이즈 (RIIZE)", "6", "다수 리스팅", "SM 신인 그룹"],
      ["박지훈", "6", "다수 리스팅", "Solo 가수"],
    ],
    [2200, 1800, 2000, 3360]
  ),
  body(""),
  h2("2-2. 아웃라이어 제거: Winsorize (P10~P90)"),
  body("재판매 가격 데이터는 우측으로 강하게 치우친(right-skewed) 분포를 보여, IQR 방식이 실질적으로 아웃라이어를 제거하지 못하는 문제가 발견되었습니다."),
  body("IQR 방식의 한계 (실제 데이터 예):"),
  bullet("Q3 = 55만원, IQR = 30만원 → 상한 = 55 + 1.5×30 = 100만원"),
  bullet("실제 최댓값 = 99.99만원 → 제거 건수: 0건"),
  body("해결책: P10~P90 Winsorize 적용"),
  formula("P10 ≤ listing_price ≤ P90"),
  body("→ 하위 10%, 상위 10% 극단값을 절삭하여 회귀 모델 안정성 확보"),
  body(""),
  h2("2-3. 피처 엔지니어링"),
  makeTable(
    ["피처", "설명", "수식/방법"],
    [
      ["d_day", "공연까지 남은 일수", "D-60, D-30, D-14, D-7, D-1"],
      ["W_g", "좌석 등급 가중치", "A(VIP)=1.4, B(R/S)=1.0, C(일반)=0.7"],
      ["popularity_score", "인기도 점수 (1~7)", "Instagram 팔로워 수 기반 매핑"],
      ["kopis_booking_rate", "예매율 근사치", "d_day 구간별 경험적 값"],
    ],
    [1800, 3000, 4560]
  ),
  body(""),
  h2("2-4. 인기도 점수 매핑표"),
  makeTable(
    ["팔로워 수 (만명)", "인기도 점수", "예시 아티스트"],
    [
      ["0 ~ 10", "1", "신인 가수"],
      ["10 ~ 25", "2", "인디 가수"],
      ["25 ~ 40", "3", "중소형 아티스트"],
      ["40 ~ 100", "4", "중견 가수"],
      ["100 ~ 250", "5", "양요섭 (282만)"],
      ["250 ~ 1,000", "6", "라이즈, 박지훈"],
      ["1,000 이상", "7", "도겸x승관 (SEVENTEEN 1,616만)"],
    ],
    [2500, 2000, 4860]
  ),
  body(""),

  pageBreak(),

  // ── 3. 모델 설계 ──
  h1("3. 모델 설계: LangGraph 5-노드 파이프라인"),
  h2("3-1. 전체 아키텍처"),
  body("LangGraph StateGraph를 활용하여 5개 노드가 순차적으로 실행되는 AI 에이전트 파이프라인을 구성하였습니다."),
  formula("입력(Input) → 좌석(Seat) → 회귀(Regression) → LP최적화(LP) → 보고서(Report)"),
  body(""),
  makeTable(
    ["노드", "역할", "핵심 출력"],
    [
      ["1. input_agent", "콘서트 정보 수집 및 검증", "concert_info (아티스트, 총 좌석, D-day 등)"],
      ["2. seat_agent", "좌석 배치도 파싱 및 등급 가중치 산출", "seat_weights {zones: {A, B, C}}"],
      ["3. regression_agent", "WTP 분포 추정 (선형 회귀)", "mu_final, sigma, beta_coefficients"],
      ["4. lp_agent", "Joint LP 최적화", "pricing_result {D-day별 최적 가격}"],
      ["5. report_agent", "시각화 및 KPI 계산", "charts, revenue_comparison, insight"],
    ],
    [2200, 2800, 4360]
  ),
  body(""),
  h2("3-2. WTP 수요 함수"),
  body("소비자의 지불의향(WTP)이 정규분포를 따른다고 가정하면, 가격 Pt에서의 수요는:"),
  formula("Qt = N × (1 - Φ((Pt - μ_adj) / σ))"),
  body("여기서:"),
  makeTable(
    ["기호", "의미"],
    [
      ["Qt", "D-day t에서의 예상 판매량"],
      ["N", "총 좌석 수"],
      ["Φ(·)", "표준정규분포 누적분포함수 (CDF)"],
      ["Pt", "D-day t에서 책정된 가격"],
      ["μ_adj", "D-day 조정 평균 WTP (= μ_final × D_factor_t)"],
      ["σ", "WTP 표준편차 (회귀 학습값)"],
    ],
    [1500, 7860]
  ),
  body(""),
  h2("3-3. D-factor: 시간 기반 WTP 조정"),
  body("공연일에 가까울수록 팬의 구매 긴박감이 높아져 WTP가 상승하는 현상을 D-factor로 모델링합니다."),
  formula("D_factor_t = clamp(1.0 + (β₁/μ) × (14 - Dt), 0.5, 1.5)"),
  body("→ D14(14일 전)를 기준점(D_factor=1.0)으로 설정"),
  bullet("D-day가 클수록 (멀수록): D_factor < 1.0 → 낮은 WTP"),
  bullet("D-day가 작을수록 (가까울수록): D_factor > 1.0 → 높은 WTP"),
  bullet("범위 제한: [0.5, 1.5] → 극단적 가격 발산 방지"),
  body(""),

  pageBreak(),

  // ── 4. 최적화 방법론 ──
  h1("4. 최적화 방법론: Joint LP"),
  h2("4-1. 문제 설정"),
  body("기존 구간별 독립 LP의 한계: 각 D-day 구간을 독립적으로 최적화하면 총 수요가 총 좌석을 초과하는 과적 문제가 발생합니다."),
  body("해결책: 모든 D-day 구간을 동시에 최적화하는 Joint LP를 구성합니다."),
  body(""),
  h2("4-2. Joint LP 수식"),
  formula("max Σ_t Σ_p  p · Qt(p) · x_{t,p}"),
  body(""),
  body("제약 조건:"),
  formula("Σ_t Σ_p  Qt(p) · x_{t,p}  ≤  N          (공유 좌석 제약)"),
  formula("Σ_p  x_{t,p}  =  1   for all t    (구간별 가격 1개 선택)"),
  formula("x_{t,p}  ∈  {0, 1}                (Binary 결정 변수)"),
  body(""),
  makeTable(
    ["변수/파라미터", "의미"],
    [
      ["x_{t,p}", "D-day t에서 가격 p를 선택하면 1, 아니면 0 (Binary)"],
      ["Qt(p)", "D-day t, 가격 p에서의 WTP 수요량"],
      ["N", "총 좌석 수 (공유 자원)"],
      ["t", "D-day 구간 인덱스 (D60, D30, D14, D7, D1)"],
      ["p", "가격 후보 (floor~ceiling 구간 20개 균등 분할)"],
    ],
    [2200, 7160]
  ),
  body(""),
  h2("4-3. 핵심 혁신: 공유 좌석 제약"),
  body("기존 독립 LP는 동일한 좌석을 여러 D-day에서 중복 판매하는 문제가 있었습니다. Joint LP의 공유 좌석 제약(Σ Qt ≤ N)은:"),
  bullet("D-60에 싸게 많이 파는 전략 vs D-1에 비싸게 적게 파는 전략 간의 trade-off를 명시적으로 모델링"),
  bullet("전체 기간 통합 수익을 전역 최적화"),
  bullet("남은 좌석을 다음 구간으로 자동 이월"),
  body(""),
  h2("4-4. 남은 좌석 추적 (실제 판매 시뮬레이션)"),
  body("LP 결과를 실제 판매에 적용할 때, 각 구간별 실제 판매량을 추적합니다."),
  formula("actual_sold_t = min(Qt(p*_t), remaining_t)"),
  formula("remaining_{t+1} = remaining_t - actual_sold_t"),
  body("→ 수익 과대계산 방지 및 현실적인 재고 관리 구현"),
  body(""),

  pageBreak(),

  // ── 5. 구현 ──
  h1("5. 구현 및 시스템 구성"),
  h2("5-1. 기술 스택"),
  makeTable(
    ["구성 요소", "기술", "역할"],
    [
      ["AI 에이전트 프레임워크", "LangGraph (StateGraph)", "5-노드 파이프라인 오케스트레이션"],
      ["최적화 솔버", "PuLP + CBC", "Joint LP 문제 풀이"],
      ["회귀 모델", "scikit-learn (LinearRegression)", "WTP 파라미터 추정"],
      ["교차검증", "GroupKFold (LOGO CV)", "아티스트 그룹 기반 일반화 검증"],
      ["UI 대시보드", "Streamlit", "실시간 파라미터 입력 및 결과 시각화"],
      ["시각화", "matplotlib", "수요 곡선, 전략 비교 차트"],
      ["데이터 처리", "pandas + numpy", "전처리, 피처 엔지니어링"],
    ],
    [2500, 2500, 4360]
  ),
  body(""),
  h2("5-2. Streamlit 대시보드 탭 구성"),
  makeTable(
    ["탭", "기능"],
    [
      ["가격표", "최종 예상 수익(단일 값) + 좌석별 최적 가격표"],
      ["수익 분석", "동적 가격 vs 정적 가격 vs 기준 전략 3자 비교"],
      ["3전략 비교", "D-day별 판매량, 잔여 좌석, 누적 수익 시각화"],
      ["민감도 시나리오", "WTP 변화에 따른 수익 민감도 분석"],
      ["D-day별 가격", "각 D-day 시점 잔여 좌석, 예상 판매량, 좌석별 가격표"],
      ["AI 해설", "LLM 기반 전략 인사이트 자동 생성"],
      ["모델 수식", "WTP 수요함수, D-factor, LP 수식 수학적 설명"],
    ],
    [2200, 7160]
  ),
  body(""),

  pageBreak(),

  // ── 6. 결과 분석 ──
  h1("6. 결과 분석 및 검증"),
  h2("6-1. 3전략 비교 프레임워크"),
  makeTable(
    ["전략", "설명", "기대 효과"],
    [
      ["전략 1: 동적 가격 (본 모델)", "Joint LP로 D-day별 최적 가격 책정", "수익 극대화, 잔여석 최소화"],
      ["전략 2: 최적 정적 가격", "단일 고정가로 전체 기간 판매", "단순 비교 기준"],
      ["전략 3: 공식가 고정", "기존 주최사 방식 (현행 유지)", "현재 상태 기준선"],
    ],
    [2500, 3000, 3860]
  ),
  body(""),
  h2("6-2. KPI 지표"),
  bullet("총 예상 수익 (원): 전략별 비교"),
  bullet("수익 개선율 (%): (동적 수익 - 기준 수익) / 기준 수익 × 100"),
  bullet("좌석 점유율 (%): 최종 판매량 / 총 좌석 × 100"),
  bullet("LOGO MAPE: 아티스트 그룹 기반 교차검증 오차"),
  body(""),
  h2("6-3. 모델 검증 방법론"),
  body("LOGO CV (Leave-One-Group-Out Cross Validation)"),
  bullet("아티스트 그룹을 기준으로 훈련/검증 분리"),
  bullet("데이터가 적은 K-pop 시장 특성상 가장 현실적인 일반화 성능 측정 방법"),
  bullet("MAPE (Mean Absolute Percentage Error) 로 예측 정확도 정량화"),
  body(""),

  pageBreak(),

  // ── 7. 결론 및 향후 ──
  h1("7. 결론 및 한계점/향후 연구"),
  h2("7-1. 핵심 기여"),
  bullet("실제 크롤링 데이터 기반 WTP 정규분포 모델 구축"),
  bullet("D-factor를 통한 시간적 WTP 변화 모델링"),
  bullet("Joint LP로 전체 판매 기간 통합 최적화 (기존 독립 LP 대비 이론적 우위)"),
  bullet("남은 좌석 추적을 통한 현실적인 수익 예측"),
  bullet("Streamlit 기반 실무 적용 가능한 대시보드 제공"),
  body(""),
  h2("7-2. 한계점"),
  makeTable(
    ["한계", "원인", "영향"],
    [
      ["데이터 부족", "티켓베이 데이터 4개 아티스트만 확보", "회귀 모델 일반화 성능 제한"],
      ["WTP 프록시 오차", "공식가 아닌 재판매가를 WTP로 사용", "실제 구매 의향 과대 추정 가능"],
      ["수요 독립성 가정", "구간별 WTP가 독립이라 가정", "앞 구간 판매가 뒤 구간 WTP 영향 미고려"],
      ["단일 공연장 가정", "좌석 배치는 텍스트 파싱에 의존", "복잡한 다층 공연장 적용 어려움"],
    ],
    [2000, 3200, 4160]
  ),
  body(""),
  h2("7-3. 향후 연구 방향"),
  bullet("KOPIS API 연동: 실시간 공식 예매율 데이터로 WTP 모델 개선"),
  bullet("수요 상호의존성 모델링: 구간 간 WTP 전이 효과 반영 (Dynamic Programming)"),
  bullet("강화학습 도입: 실제 판매 결과 피드백으로 가격 전략 지속 학습"),
  bullet("데이터 확장: 더 많은 아티스트 및 장르로 일반화 성능 향상"),
  bullet("공정성 제약 추가: 저소득 팬을 위한 최저가 좌석 보장 조건 LP에 통합"),
  body(""),
  body(""),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 480 },
    border: { top: { style: BorderStyle.SINGLE, size: 6, color: "1F3864", space: 1 } },
    children: [new TextRun({ text: "UNIST IE209 — K-pop Concert Dynamic Pricing AI Agent", size: 20, font: "맑은 고딕", color: "595959" })],
  }),
];

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "-",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 600, hanging: 300 } } },
        }],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: "맑은 고딕", size: 22 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "맑은 고딕", color: "1F3864" },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "맑은 고딕", color: "2E75B6" },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [new TextRun({ text: "IE209 | K-pop 콘서트 동적 가격 책정 AI 에이전트", size: 18, font: "맑은 고딕", color: "595959" })],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "1F3864", space: 1 } },
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "- ", size: 18, font: "맑은 고딕", color: "595959" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "맑은 고딕", color: "595959" }),
            new TextRun({ text: " -", size: 18, font: "맑은 고딕", color: "595959" }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:\\Users\\sjsss\\Downloads\\pricing_agent\\IE209_발표내용.docx", buffer);
  console.log("완료: IE209_발표내용.docx 생성됨");
});
