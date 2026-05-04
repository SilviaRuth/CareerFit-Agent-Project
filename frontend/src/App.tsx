import { useState } from "react";
import { AnalysisPage } from "./pages/AnalysisPage";
import { InputPage } from "./pages/InputPage";
import type { AnalysisResult } from "./types/analysis";

export default function App() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  if (analysisResult) {
    return (
      <AnalysisPage
        result={analysisResult}
        onStartOver={() => {
          setAnalysisResult(null);
        }}
      />
    );
  }

  return <InputPage onAnalysisComplete={setAnalysisResult} />;
}
