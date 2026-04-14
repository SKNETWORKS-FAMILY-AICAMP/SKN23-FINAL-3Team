import { useMemo, useRef, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  ReferenceLine,
} from "recharts";

interface UserProfile {
  name: string;
  breed: string;
  age: string;
  gender: string;
  status: string;
  profileImageUrl?: string;
}

const PROFILE: UserProfile = {
  name: "콩이",
  breed: "포메라니안",
  age: "4살",
  gender: "여아",
  status: "정상",
  profileImageUrl: undefined,
};

const WEIGHT_HISTORY = [
  { week: "5주전", value: 4.9 },
  { week: "4주전", value: 4.8 },
  { week: "3주전", value: 4.7 },
  { week: "2주전", value: 4.6 },
  { week: "1주전", value: 4.6 },
  { week: "현재", value: 4.8 },
];

const BCS_HISTORY = [
  { round: "1차", score: 6 },
  { round: "2차", score: 5 },
  { round: "3차", score: 6 },
];

const WEEKLY_TREND = [
  { day: "월", weight: 4.85, target: 4.6 },
  { day: "화", weight: 4.83, target: 4.6 },
  { day: "수", weight: 4.81, target: 4.6 },
  { day: "목", weight: 4.8, target: 4.6 },
  { day: "금", weight: 4.79, target: 4.6 },
  { day: "토", weight: 4.78, target: 4.6 },
  { day: "일", weight: 4.8, target: 4.6 },
];

const ACTIVITY_DATA = [
  { name: "산책", value: 40, color: "#D85A30" },
  { name: "식단", value: 35, color: "#EF9F27" },
  { name: "휴식", value: 25, color: "#5DCAA5" },
];

const DIARY_ITEMS = [
  { label: "사료 2회 급여", done: true },
  { label: "간식 1회", done: true },
  { label: "산책 25분", done: true },
  { label: "몸무게 기록", done: true },
];

const C = {
  coral400: "#D85A30",
  coral100: "#F5C4B3",
  coral50: "#FAECE7",
  coral800: "#712B13",
  amber400: "#EF9F27",
  amber50: "#FAEEDA",
  amber100: "#FAC775",
  amber800: "#633806",
  teal400: "#5DCAA5",
  teal50: "#E1F5EE",
  teal100: "#9FE1CB",
  teal800: "#085041",
  gray50: "#F1EFE8",
  gray100: "#D3D1C7",
  gray400: "#888780",
  gray800: "#2C2C2A",
  pink50: "#FBEAF0",
  pink100: "#F4C0D1",
  pink800: "#72243E",
} as const;

function Tag({
  children,
  variant = "coral",
}: {
  children: React.ReactNode;
  variant?: "coral" | "amber" | "teal" | "pink" | "gray";
}) {
  const styles: Record<string, React.CSSProperties> = {
    coral: {
      background: C.coral50,
      color: C.coral800,
      borderColor: C.coral100,
    },
    amber: {
      background: C.amber50,
      color: C.amber800,
      borderColor: C.amber100,
    },
    teal: {
      background: C.teal50,
      color: C.teal800,
      borderColor: C.teal100,
    },
    pink: {
      background: C.pink50,
      color: C.pink800,
      borderColor: C.pink100,
    },
    gray: {
      background: C.gray50,
      color: C.gray800,
      borderColor: C.gray100,
    },
  };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        borderRadius: 999,
        padding: "4px 9px",
        fontSize: 11,
        fontWeight: 600,
        border: "0.5px solid",
        whiteSpace: "nowrap",
        ...styles[variant],
      }}
    >
      {children}
    </span>
  );
}

function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={{
        background: "#fff",
        border: "0.5px solid rgba(0,0,0,0.08)",
        borderRadius: 18,
        padding: 18,
        boxShadow: "0 6px 20px rgba(0,0,0,0.03)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function CardLabel({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    null
  );
}

function ProfileAvatar({
  imageUrl,
  name,
  size = 48,
}: {
  imageUrl?: string;
  name: string;
  size?: number;
}) {
  const [imgError, setImgError] = useState(false);
  const initials = name.slice(0, 1);

  const containerStyle: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: "50%",
    flexShrink: 0,
    overflow: "hidden",
    border: `0.5px solid ${C.coral100}`,
    background: C.coral50,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };

  if (imageUrl && !imgError) {
    return (
      <div style={containerStyle}>
        <img
          src={imageUrl}
          alt={`${name} 프로필 사진`}
          onError={() => setImgError(true)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <span
        style={{
          fontSize: size * 0.38,
          fontWeight: 700,
          color: C.coral800,
          userSelect: "none",
        }}
      >
        {initials}
      </span>
    </div>
  );
}

function ServiceActionCard({
  title,
  desc,
  badge,
}: {
  title: string;
  desc: string;
  badge: string;
}) {
  return (
    <Card style={{ minWidth: 0, padding: 16 }}>
      <Tag variant="coral">{badge}</Tag>
      <p
        style={{
          fontSize: 15,
          fontWeight: 700,
          color: "#111",
          marginTop: 12,
          marginBottom: 6,
        }}
      >
        {title}
      </p>
      <p
        style={{
          fontSize: 12,
          color: C.gray400,
          lineHeight: 1.6,
          wordBreak: "keep-all",
        }}
      >
        {desc}
      </p>
    </Card>
  );
}

function ServiceStatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <Card style={{ padding: 16 }}>
      <p
        style={{
          fontSize: 11,
          color: C.gray400,
          marginBottom: 8,
        }}
      >
        {label}
      </p>
      <p
        style={{
          fontSize: 24,
          fontWeight: 700,
          color: "#111",
          marginBottom: 4,
        }}
      >
        {value}
      </p>
      <p
        style={{
          fontSize: 12,
          color: C.gray400,
          lineHeight: 1.5,
        }}
      >
        {sub}
      </p>
    </Card>
  );
}

function SectionTitle({
  title,
  desc,
}: {
  title: string;
  desc: string;
}) {
  return (
    <div style={{ marginTop: 4, marginBottom: 2 }}>
      <h2
        style={{
          fontSize: 18,
          fontWeight: 700,
          color: "#111",
          marginBottom: 4,
        }}
      >
        {title}
      </h2>
      <p
        style={{
          fontSize: 13,
          color: C.gray400,
          lineHeight: 1.6,
        }}
      >
        {desc}
      </p>
    </div>
  );
}

function LegendDot({
  color,
  label,
  dashed,
}: {
  color: string;
  label: string;
  dashed?: boolean;
}) {
  return (
    <span
      style={{
        display: "flex",
        alignItems: "center",
        gap: 5,
        fontSize: 12,
        color: C.gray400,
      }}
    >
      {dashed ? (
        <span
          style={{
            width: 16,
            height: 2,
            borderTop: `2px dashed ${color}`,
            display: "inline-block",
          }}
        />
      ) : (
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: 2,
            background: color,
            display: "inline-block",
          }}
        />
      )}
      {label}
    </span>
  );
}

function CheckCircle() {
  return (
    <div
      style={{
        width: 18,
        height: 18,
        borderRadius: "50%",
        background: C.teal50,
        border: `0.5px solid ${C.teal100}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg width="9" height="7" viewBox="0 0 9 7" fill="none">
        <path
          d="M1 3.5L3.5 6L8 1"
          stroke={C.teal800}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function WeightCard() {
  const [inputVal, setInputVal] = useState("4.8");
  const [savedVal, setSavedVal] = useState(4.6);
  const [displayVal, setDisplayVal] = useState(4.8);

  const weightData = useMemo(() => {
    const base = WEIGHT_HISTORY.slice(0, -1);
    const current = parseFloat(inputVal) || 4.8;
    return [...base, { week: "현재", value: current }];
  }, [inputVal]);

  const isChanged = parseFloat(inputVal) !== savedVal;
  const currentWeight = parseFloat(inputVal) || 4.8;
  const targetWeight = 4.6;
  const diffFromTarget = Math.max(0, currentWeight - targetWeight).toFixed(1);

  function handleSave() {
    const v = parseFloat(inputVal);
    if (isNaN(v)) return;
    setSavedVal(v);
    setDisplayVal(v);
  }

  return (
    <Card
      style={{
        padding: 20,
        borderRadius: 20,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div>
          <p
            style={{
              margin: 0,
              fontSize: 12,
              fontWeight: 700,
              color: C.gray400,
              marginBottom: 6,
              letterSpacing: "0.2px",
            }}
          >
            TODAY LOG
          </p>

          <h3
            style={{
              margin: 0,
              fontSize: 20,
              fontWeight: 800,
              color: "#111",
              lineHeight: 1.25,
            }}
          >
            오늘의 몸무게 기록
          </h3>

          <p
            style={{
              margin: "6px 0 0",
              fontSize: 13,
              color: C.gray400,
              lineHeight: 1.6,
            }}
          >
            오늘 측정한 몸무게를 입력하고 변화 흐름을 확인해보세요.
          </p>
        </div>

        <Tag variant="amber">표준보다 약간 높음</Tag>
      </div>

      <div
        style={{
          background: "#FCFBF9",
          border: "1px solid rgba(0,0,0,0.05)",
          borderRadius: 18,
          padding: 16,
          marginBottom: 14,
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) auto",
            gap: 12,
            alignItems: "center",
          }}
        >
          <div>
            <p
              style={{
                margin: "0 0 8px",
                fontSize: 12,
                color: C.gray400,
                fontWeight: 600,
              }}
            >
              입력할 몸무게
            </p>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                background: "#fff",
                border: `1px solid ${isChanged ? C.coral100 : "rgba(0,0,0,0.08)"}`,
                boxShadow: isChanged ? "0 0 0 4px rgba(216,90,48,0.06)" : "none",
                borderRadius: 16,
                padding: "12px 14px",
              }}
            >
              <input
                type="number"
                step={0.1}
                min={1}
                max={20}
                value={inputVal}
                onChange={(e) => {
                  setInputVal(e.target.value);
                  const v = parseFloat(e.target.value);
                  if (!isNaN(v)) setDisplayVal(v);
                }}
                style={{
                  width: "100%",
                  border: "none",
                  outline: "none",
                  background: "transparent",
                  fontSize: 34,
                  fontWeight: 800,
                  color: "#111",
                  lineHeight: 1,
                  padding: 0,
                  fontFamily: "inherit",
                }}
              />
              <span
                style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color: C.gray400,
                  flexShrink: 0,
                }}
              >
                kg
              </span>
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={!isChanged}
            style={{
              height: 58,
              minWidth: 96,
              border: "none",
              borderRadius: 14,
              padding: "0 18px",
              background: isChanged ? C.coral400 : "#ECE9E2",
              color: isChanged ? "#fff" : C.gray400,
              fontSize: 14,
              fontWeight: 700,
              cursor: isChanged ? "pointer" : "default",
              boxShadow: isChanged ? "0 10px 20px rgba(216,90,48,0.18)" : "none",
              whiteSpace: "nowrap",
            }}
          >
            저장
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 8,
            marginTop: 12,
          }}
        >
          <div
            style={{
              background: "#fff",
              border: "1px solid rgba(0,0,0,0.05)",
              borderRadius: 14,
              padding: "10px 12px",
            }}
          >
            <p
              style={{
                margin: "0 0 4px",
                fontSize: 11,
                color: C.gray400,
              }}
            >
              오늘 표시값
            </p>
            <p
              style={{
                margin: 0,
                fontSize: 18,
                fontWeight: 800,
                color: "#111",
              }}
            >
              {displayVal.toFixed(1)}kg
            </p>
          </div>

          <div
            style={{
              background: "#fff",
              border: "1px solid rgba(0,0,0,0.05)",
              borderRadius: 14,
              padding: "10px 12px",
            }}
          >
            <p
              style={{
                margin: "0 0 4px",
                fontSize: 11,
                color: C.gray400,
              }}
            >
              마지막 저장값
            </p>
            <p
              style={{
                margin: 0,
                fontSize: 18,
                fontWeight: 800,
                color: "#111",
              }}
            >
              {savedVal.toFixed(1)}kg
            </p>
          </div>

          <div
            style={{
              background: "#fff",
              border: "1px solid rgba(0,0,0,0.05)",
              borderRadius: 14,
              padding: "10px 12px",
            }}
          >
            <p
              style={{
                margin: "0 0 4px",
                fontSize: 11,
                color: C.gray400,
              }}
            >
              목표까지
            </p>
            <p
              style={{
                margin: 0,
                fontSize: 18,
                fontWeight: 800,
                color: C.coral400,
              }}
            >
              {diffFromTarget}kg
            </p>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 4 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 8,
            gap: 8,
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 13,
              fontWeight: 700,
              color: "#111",
            }}
          >
            최근 6주 변화
          </p>

          <span
            style={{
              fontSize: 11,
              color: C.gray400,
            }}
          >
            저장값 기준 {savedVal.toFixed(1)}kg
          </span>
        </div>

        <ResponsiveContainer width="100%" height={86}>
          <AreaChart
            data={weightData}
            margin={{ top: 6, right: 4, left: -28, bottom: 0 }}
          >
            <defs>
              <linearGradient id="wGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={C.coral400} stopOpacity={0.16} />
                <stop offset="95%" stopColor={C.coral400} stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(0,0,0,0.05)"
              vertical={false}
            />

            <XAxis
              dataKey="week"
              tick={{ fontSize: 10, fill: C.gray400 }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              domain={[4.3, 5.1]}
              tick={{ fontSize: 10, fill: C.gray400 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => v.toFixed(1)}
            />

            <Tooltip
              contentStyle={{
                fontSize: 12,
                borderRadius: 10,
                border: "0.5px solid rgba(0,0,0,0.1)",
                boxShadow: "0 8px 18px rgba(0,0,0,0.06)",
              }}
              formatter={(v: number) => [`${v.toFixed(1)} kg`, "몸무게"]}
            />

            <Area
              type="monotone"
              dataKey="value"
              stroke={C.coral400}
              strokeWidth={2.2}
              fill="url(#wGrad)"
              dot={{ r: 3, fill: C.coral400 }}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>

        <div
          style={{
            marginTop: 10,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 12,
              color: C.gray400,
              lineHeight: 1.6,
            }}
          >
            최근 흐름은 안정적이고, 목표 몸무게까지 천천히 줄여가면 좋아요.
          </p>

          <Tag variant="coral">기록 유지 중</Tag>
        </div>
      </div>
    </Card>
  );
}

function BcsCard() {
  const avg = (
    BCS_HISTORY.reduce((sum, item) => sum + item.score, 0) /
    BCS_HISTORY.length
  ).toFixed(1);

  const latestScore = BCS_HISTORY[BCS_HISTORY.length - 1]?.score ?? 0;
  const scoreLabel =
    Number(avg) >= 7 ? "비만 경향" :
    Number(avg) >= 6 ? "과체중 경향" :
    Number(avg) >= 4 ? "대체로 정상 범위" :
    "저체중 경향";

  return (
    <Card
      style={{
        padding: 20,
        borderRadius: 20,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 16,
          marginBottom: 16,
        }}
      >
        <div style={{ minWidth: 0 }}>
          <p
            style={{
              fontSize: 16,
              fontWeight: 700,
              color:"#111",
              margin: 0,
              marginBottom: 6,
            }}
          >
            BCS 주간 평균 점수
          </p>

          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 8,
              marginBottom: 8,
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                fontSize: 40,
                fontWeight: 800,
                lineHeight: 1,
                color: C.coral400,
              }}
            >
              {avg}
            </span>
            <span
              style={{
                fontSize: 18,
                fontWeight: 700,
                color: C.gray400,
              }}
            >
              / 9
            </span>
          </div>

          <p
            style={{
              fontSize: 12,
              color: C.gray400,
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            최근 측정 3회의 평균 체형 점수예요.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-end",
            gap: 8,
            flexShrink: 0,
          }}
        >
          <Tag variant="amber">최근 3회 평균</Tag>
          <Tag variant="gray">{scoreLabel}</Tag>
        </div>
      </div>

      <div
        style={{
          background: "#FCFBF9",
          border: "1px solid rgba(0,0,0,0.05)",
          borderRadius: 16,
          padding: "14px 14px 10px",
          marginBottom: 12,
        }}
      >
        <ResponsiveContainer width="100%" height={140}>
          <BarChart
            data={BCS_HISTORY}
            margin={{ top: 8, right: 8, left: -20, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(0,0,0,0.05)"
              vertical={false}
            />
            <XAxis
              dataKey="round"
              tick={{ fontSize: 11, fill: C.gray400 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, 9]}
              ticks={[0, 3, 6, 9]}
              tick={{ fontSize: 10, fill: C.gray400 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: "rgba(0,0,0,0.03)" }}
              contentStyle={{
                fontSize: 12,
                borderRadius: 10,
                border: "0.5px solid rgba(0,0,0,0.1)",
                boxShadow: "0 8px 20px rgba(0,0,0,0.06)",
              }}
              formatter={(v: number) => [`${v}점`, "BCS"]}
            />
            <Bar dataKey="score" radius={[8, 8, 0, 0]} barSize={56}>
              {BCS_HISTORY.map((d, i) => (
                <Cell
                  key={`bcs-bar-${d.round}-${i}`}
                  fill={i === 1 ? C.amber400 : C.coral400}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: 8,
        }}
      >
        {BCS_HISTORY.map((d, i) => {
          const isLatest = i === BCS_HISTORY.length - 1;

          return (
            <div
              key={`bcs-summary-${d.round}-${i}`}
              style={{
                background: isLatest ? "#FFF4EE" : "#F8F7F4",
                border: isLatest
                  ? `1px solid ${C.coral100}`
                  : "1px solid rgba(0,0,0,0.04)",
                borderRadius: 14,
                padding: "12px 12px 10px",
              }}
            >
              <p
                style={{
                  fontSize: 11,
                  color: C.gray400,
                  margin: 0,
                  marginBottom: 6,
                }}
              >
                {d.round}
              </p>

              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 800,
                    color: isLatest ? C.coral400 : "#111",
                    lineHeight: 1.1,
                  }}
                >
                  {d.score}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    color: C.gray400,
                    fontWeight: 600,
                  }}
                >
                  점
                </span>
              </div>

              {isLatest && (
                <p
                  style={{
                    fontSize: 11,
                    color: C.coral800,
                    margin: 0,
                    marginTop: 6,
                    fontWeight: 600,
                  }}
                >
                  최신 측정값
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div
        style={{
          marginTop: 12,
          paddingTop: 12,
          borderTop: "1px solid rgba(0,0,0,0.06)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <p
          style={{
            fontSize: 12,
            color: C.gray400,
            margin: 0,
            lineHeight: 1.6,
          }}
        >
          최신 점수는 <span style={{ color: "#111", fontWeight: 700 }}>{latestScore}점</span>이고,
          전체 평균은 <span style={{ color: C.coral400, fontWeight: 800 }}>{avg} / 9</span>예요.
        </p>

        <Tag variant="coral">체형 변화 추적 중</Tag>
      </div>
    </Card>
  );
}

function TrendCard() {
  return (
    <Card style={{ gridColumn: "1 / -1" }}>
      <CardLabel>몸무게 주간 트렌드</CardLabel>

      <div
        style={{ display: "flex", gap: 14, marginBottom: 10 }}
      >
        <p
          style={{
            fontSize: 16,
            fontWeight: 700,
            color: "#111",
            marginBottom: 6,
          }}
        >
          실제 몸무게 vs 목표 몸무게
        </p>
        <LegendDot color={C.coral400} label="실제 몸무게" />
        <LegendDot
          color={C.teal400}
          label="목표 몸무게"
          dashed
        />
      </div>

      <ResponsiveContainer width="100%" height={190}>
        <LineChart
          data={WEEKLY_TREND}
          margin={{ top: 12, right: 12, left: -20, bottom: 4 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(0,0,0,0.05)"
            vertical={false}
          />

          <XAxis
            dataKey="day"
            tick={{ fontSize: 11, fill: C.gray400 }}
            axisLine={false}
            tickLine={false}
          />

          <YAxis
            domain={[4.4, 5.0]}
            tick={{ fontSize: 10, fill: C.gray400 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${v.toFixed(1)}kg`}
          />

          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "0.5px solid rgba(0,0,0,0.1)",
            }}
            formatter={(v: number, name: string) => [
              `${v.toFixed(2)} kg`,
              name === "weight" ? "실제 몸무게" : "목표 몸무게",
            ]}
          />

          {/* 목표 몸무게 기준선 */}
          <ReferenceLine
            y={4.6}
            stroke={C.teal400}
            strokeWidth={2.5}
            strokeDasharray="6 4"
            ifOverflow="extendDomain"
            label={{
              value: "목표 4.6kg",
              position: "insideBottomRight",
              fill: C.teal800,
              fontSize: 11,
            }}
          />

          <Line
            type="monotone"
            dataKey="weight"
            name="weight"
            stroke={C.coral400}
            strokeWidth={2.5}
            dot={{ r: 3, fill: C.coral400 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

function DiaryCard() {
  return (
    <Card>
      <CardLabel>오늘의 기록</CardLabel>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {DIARY_ITEMS.map((item, i) => (
          <div
            key={`diary-${item.label}-${i}`}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "9px 0",
              borderBottom:
                i < DIARY_ITEMS.length - 1
                  ? "0.5px solid rgba(0,0,0,0.07)"
                  : "none",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <CheckCircle />
              <span style={{ fontSize: 13, color: "#111" }}>
                {item.label}
              </span>
            </div>
            <span
              style={{
                fontSize: 11,
                color: C.teal800,
                background: C.teal50,
                borderRadius: 999,
                padding: "3px 8px",
                fontWeight: 600,
              }}
            >
              완료
            </span>
          </div>
        ))}
      </div>

      <button
        style={{
          marginTop: 14,
          width: "100%",
          background: "#fff",
          color: "#111",
          border: "0.5px solid rgba(0,0,0,0.12)",
          borderRadius: 10,
          padding: "10px 12px",
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        오늘 기록 더 입력하기
      </button>
    </Card>
  );
}

function ActivityCard() {
  return (
    <Card>
      <CardLabel>건강 활동 분포</CardLabel>
      <ResponsiveContainer width="100%" height={130}>
        <PieChart>
          <Pie
            data={ACTIVITY_DATA}
            cx="50%"
            cy="50%"
            innerRadius={38}
            outerRadius={58}
            paddingAngle={3}
            dataKey="value"
          >
            {ACTIVITY_DATA.map((entry, i) => (
              <Cell
                key={`activity-cell-${entry.name}-${i}`}
                fill={entry.color}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "0.5px solid rgba(0,0,0,0.1)",
            }}
            formatter={(
              v: number,
              _: string,
              props: { payload?: { name?: string } },
            ) => [`${v}%`, props.payload?.name ?? ""]}
          />
        </PieChart>
      </ResponsiveContainer>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 5,
          marginTop: 4,
        }}
      >
        {ACTIVITY_DATA.map((d, i) => (
          <span
            key={`activity-legend-${d.name}-${i}`}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              fontSize: 12,
              color: C.gray400,
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: d.color,
                flexShrink: 0,
                display: "inline-block",
              }}
            />
            {d.name} {d.value}%
          </span>
        ))}
      </div>
    </Card>
  );
}

function AiCoachingCard() {
  const actions = [
    { label: "추천 행동 1", text: "저녁 산책 10분 추가" },
    { label: "추천 행동 2", text: "간식 오늘 1회 유지" },
  ];

  return (
    <div
      style={{
        background: C.gray800,
        border: "0.5px solid #444441",
        borderRadius: 18,
        padding: 18,
        boxShadow: "0 8px 22px rgba(0,0,0,0.08)",
      }}
    >
      <p
        style={{
          fontSize: 11,
          color: C.gray400,
          letterSpacing: "0.5px",
          textTransform: "uppercase",
          marginBottom: 8,
          fontWeight: 600,
        }}
      >
        AI 코칭
      </p>

      <p
        style={{
          fontSize: 18,
          fontWeight: 700,
          color: "#F1EFE8",
          marginBottom: 12,
        }}
      >
        오늘의 한마디
      </p>

      <div
        style={{
          background: "rgba(255,255,255,0.07)",
          border: "0.5px solid rgba(255,255,255,0.1)",
          borderRadius: 12,
          padding: "12px 14px",
          fontSize: 13,
          color: "#D3D1C7",
          lineHeight: 1.75,
          marginBottom: 12,
        }}
      >
        콩이는 지금 정상 체중이에요.
        <br />
        오늘은 산책을 10분 더 늘려볼까요?
        <br />
        간식은 1번만 유지하면 더 좋아질 거예요!
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 8,
        }}
      >
        {actions.map((a, i) => (
          <div
            key={`coach-action-${a.label}-${i}`}
            style={{
              background: "rgba(255,255,255,0.06)",
              border: "0.5px solid rgba(255,255,255,0.09)",
              borderRadius: 12,
              padding: "10px 12px",
            }}
          >
            <p
              style={{
                fontSize: 10,
                color: C.amber100,
                marginBottom: 4,
                letterSpacing: "0.4px",
                fontWeight: 600,
              }}
            >
              {a.label}
            </p>
            <p
              style={{
                fontSize: 13,
                color: "#F1EFE8",
                fontWeight: 600,
              }}
            >
              {a.text}
            </p>
          </div>
        ))}
      </div>

      <button
        style={{
          marginTop: 14,
          width: "100%",
          background: "#fff",
          color: C.gray800,
          border: "none",
          borderRadius: 10,
          padding: "10px 12px",
          fontSize: 13,
          fontWeight: 700,
          cursor: "pointer",
        }}
      >
        AI 코칭 더 보기
      </button>
    </div>
  );
}

function CtaBanner() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        background: "#fff",
        border: "0.5px solid rgba(0,0,0,0.1)",
        borderRadius: 16,
        padding: "14px 16px",
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          background: C.coral50,
          border: `0.5px solid ${C.coral100}`,
          borderRadius: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke={C.coral400}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
      </div>

      <div style={{ flex: 1 }}>
        <p
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "#111",
            marginBottom: 2,
          }}
        >
          비만도 AI 분석
        </p>
        <p style={{ fontSize: 12, color: C.gray400 }}>
          사진으로 체형 점수 바로 확인
        </p>
      </div>

      <button
        style={{
          background: C.coral400,
          color: "#fff",
          border: "none",
          borderRadius: 8,
          padding: "8px 14px",
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
          whiteSpace: "nowrap",
          flexShrink: 0,
        }}
      >
        지금 분석 →
      </button>
    </div>
  );
}

function SecondaryBanner() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        background: "#fff",
        border: "0.5px solid rgba(0,0,0,0.1)",
        borderRadius: 16,
        padding: "14px 16px",
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          background: C.teal50,
          border: `0.5px solid ${C.teal100}`,
          borderRadius: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke={C.teal800}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 20V10" />
          <path d="M18 20V4" />
          <path d="M6 20v-6" />
        </svg>
      </div>

      <div style={{ flex: 1 }}>
        <p
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "#111",
            marginBottom: 2,
          }}
        >
          주간 헬스 다이어리 보기
        </p>
        <p style={{ fontSize: 12, color: C.gray400 }}>
          변화 추이와 추천 루틴을 요약해서 확인
        </p>
      </div>

      <button
        style={{
          background: C.teal400,
          color: "#fff",
          border: "none",
          borderRadius: 8,
          padding: "8px 14px",
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
          whiteSpace: "nowrap",
          flexShrink: 0,
        }}
      >
        다이어리 →
      </button>
    </div>
  );
}

export function HeroBanner() {
  const profileInputRef = useRef<HTMLInputElement>(null);
  const [profileImage, setProfileImage] = useState<
    string | undefined
  >(PROFILE.profileImageUrl);

  function handleProfileImageChange(
    e: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setProfileImage(url);
  }

  return (
    <div
      style={{
        background: "linear-gradient(...)",
        minHeight: "100vh",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "24px 20px",
        }}
      >
        <div
          className="mx-[0px] my-[14px] mx-[0px] mt-[30px] mb-[14px]"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            background: "#fff",
            border: "0.5px solid rgba(0,0,0,0.08)",
            borderRadius: 999,
            padding: "6px 12px",
            fontSize: 12,
            color: C.coral800,
            marginBottom: 14,
          }}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: C.coral400,
              display: "inline-block",
            }}
          />
          AI 반려견 건강관리 서비스
        </div>

        <div
          style={{
            background:
              "linear-gradient(135deg, #FFFFFF 0%, #FFF4EE 100%)",
            border: "0.5px solid rgba(0,0,0,0.08)",
            borderRadius: 24,
            padding: 24,
            marginBottom: 14,
            boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
          }}
        >
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 18,
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ flex: "1 1 320px", minWidth: 0 }}>
              <p
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: C.coral400,
                  marginBottom: 8,
                  letterSpacing: "0.3px",
                }}
              >
                오늘의 맞춤 건강 홈
              </p>

              <h1
                style={{
                  fontSize: 30,
                  lineHeight: 1.25,
                  fontWeight: 700,
                  color: "#111",
                  marginBottom: 10,
                  wordBreak: "keep-all",
                }}
              >
                {PROFILE.name}의 건강 상태를
                <br />
                한눈에 관리해보세요
              </h1>

              <p
                style={{
                  fontSize: 14,
                  color: C.gray400,
                  lineHeight: 1.7,
                  marginBottom: 16,
                  maxWidth: 460,
                }}
              >
                비만도 분석, 몸무게 기록, 데일리 체크, AI
                코칭까지
                <br />
                반려견 맞춤 건강 루틴을 한 곳에서 이어갈 수
                있어요.
              </p>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  marginBottom: 16,
                }}
              >
                <Tag variant="coral">비만도 분석</Tag>
                <Tag variant="amber">건강 기록</Tag>
                <Tag variant="teal">AI 코칭</Tag>
                <Tag variant="pink">주간 리포트</Tag>
              </div>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 10,
                }}
              >
                <button
                  style={{
                    background: C.coral400,
                    color: "#fff",
                    border: "none",
                    borderRadius: 10,
                    padding: "11px 16px",
                    fontSize: 14,
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  비만도 분석 시작하기
                </button>
                <button
                  style={{
                    background: "#fff",
                    color: "#111",
                    border: "0.5px solid rgba(0,0,0,0.12)",
                    borderRadius: 10,
                    padding: "11px 16px",
                    fontSize: 14,
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  오늘 기록 입력하기
                </button>
              </div>
            </div>

            <div
              style={{
                flex: "0 0 220px",
                background: "#fff",
                border: "0.5px solid rgba(0,0,0,0.08)",
                borderRadius: 18,
                padding: 16,
              }}
            >
              <p
                style={{
                  fontSize: 11,
                  color: C.gray400,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  marginBottom: 12,
                  fontWeight: 600,
                }}
              >
                반려견 프로필
              </p>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <div style={{ position: "relative" }}>
                  <ProfileAvatar
                    imageUrl={profileImage}
                    name={PROFILE.name}
                    size={56}
                  />
                  <button
                    onClick={() =>
                      profileInputRef.current?.click()
                    }
                    title="프로필 사진 변경"
                    style={{
                      position: "absolute",
                      bottom: -2,
                      right: -2,
                      width: 22,
                      height: 22,
                      borderRadius: "50%",
                      background: C.coral400,
                      border: "1.5px solid #fff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      padding: 0,
                    }}
                  >
                    <svg
                      width="10"
                      height="10"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="#fff"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M9 1.5l1.5 1.5L4 9.5H2.5V8L9 1.5z" />
                    </svg>
                  </button>
                  <input
                    ref={profileInputRef}
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    onChange={handleProfileImageChange}
                  />
                </div>

                <div>
                  <p
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: "#111",
                    }}
                  >
                    {PROFILE.name}
                  </p>
                  <p
                    style={{
                      fontSize: 12,
                      color: C.gray400,
                      marginTop: 2,
                    }}
                  >
                    {PROFILE.breed} · {PROFILE.age} ·{" "}
                    {PROFILE.gender}
                  </p>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 6,
                  marginTop: 14,
                }}
              >
                <Tag variant="gray">{PROFILE.status}</Tag>
                <Tag variant="amber">최근 분석 완료</Tag>
              </div>

              <div
                style={{
                  marginTop: 14,
                  paddingTop: 14,
                  borderTop: "0.5px solid rgba(0,0,0,0.08)",
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 10,
                }}
              >
                <div>
                  <p style={{ fontSize: 11, color: C.gray400 }}>
                    현재 몸무게
                  </p>
                  <p
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: "#111",
                      marginTop: 3,
                    }}
                  >
                    4.8kg
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: 11, color: C.gray400 }}>
                    평균 BCS
                  </p>
                  <p
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: C.coral400,
                      marginTop: 3,
                    }}
                  >
                    5 / 9
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0,1fr))",
            gap: 10,
            marginBottom: 14,
          }}
        >
          <ServiceStatCard
            label="이번 주 기록률"
            value="86%"
            sub="꾸준히 관리 중이에요"
          />
          <ServiceStatCard
            label="오늘 추천 행동"
            value="2개"
            sub="산책 + 간식 조절"
          />
          <ServiceStatCard
            label="최근 상태 요약"
            value="정상체중"
            sub="목표 체중까지 -0.2kg"
          />
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <SectionTitle
            title="건강 관리 대시보드"
            desc="측정 데이터와 기록 데이터를 함께 보며 관리할 수 있어요"
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "minmax(0,1fr) minmax(0,1fr)",
              gap: 10,
            }}
          >
            <WeightCard />
            <BcsCard />
          </div>

          <TrendCard />

          <SectionTitle
            title="오늘의 기록과 활동"
            desc="작은 기록이 쌓일수록 AI 코칭 정확도가 더 좋아져요"
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "minmax(0,1fr) minmax(0,1fr)",
              gap: 10,
            }}
          >
            <DiaryCard />
            <ActivityCard />
          </div>

          <SectionTitle
            title="맞춤 코칭"
            desc="현재 상태를 바탕으로 오늘 실천할 행동을 추천해드려요"
          />

          <AiCoachingCard />

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "minmax(0,1fr) minmax(0,1fr)",
              gap: 10,
            }}
          >
            <CtaBanner />
            <SecondaryBanner />
          </div>
        </div>
      </div>
    </div>
  );
}

export default HeroBanner;