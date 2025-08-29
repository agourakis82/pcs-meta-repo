
# PCS‑HELIO — **Ponte Epistemológica–Epidemiológica** (v1.0, 2025-08-23)

> **Propósito:** substituir analogias por *equivalências de desenho experimental*, unindo **epistemologia** (como sabemos/medimos) e **epidemiologia** (como inferimos em populações) para tornar o módulo **PCS‑HELIO** auditável, reprodutível e clinicamente audível.

---

## 1. Enunciado da Ponte

\begin{justify}
Tratamos o **clima espacial** (Kp, Dst, AE; IMF \(B_z\), velocidade/densidade do vento solar; F10.7) como um \textbf{driver exógeno} \(\mathcal{U}(t)\), objetivo e público, definido por agências oficiais (NOAA/NASA/WDC Kyoto). Este driver modula \textbf{parâmetros efetivos} \(\theta(t)\) do nosso modelo neurocomputacional-simbólico (ganho \(\beta\), ruído \(\sigma\), taxa de exploração \(\epsilon\)), que por sua vez determinam \textbf{métricas de estado} de organização cognitivo-linguística (AG5/KEC: entropia de transição \(\hat{H}\), curvatura média \(\tilde{\kappa}\), coerência \(\mathrm{Coh}\)).
\end{justify}

\begin{justify}
A ponte é \textbf{epistemológica} porque estabelece como conhecemos: partes observáveis (exposição \(\mathcal{U}(t)\), resposta \(Y(t)\)), modelos (SEA, ARIMAX/VAR Bayes, ablations) e validação (ZuCo como \emph{proxy} neurocognitivo); e é \textbf{epidemiológica} porque define como inferimos em populações: delineamentos, janelas, contrafactuais, controles sazonais/temáticos e falsificações. Não há metáfora: há \emph{equivalência de desenho} entre \emph{exposição→resposta} nos domínios físico e simbólico.
\end{justify}

---

## 2. Continuidade metodológica (Material→Informacional)

\begin{justify}
Em liberação controlada de fármacos, o \emph{perfil de exposição} determina a concentração no sítio e efeitos. Na PCS, substituímos “dose química” por \(\mathcal{U}(t)\) (excitação físico-ambiental auditável), mantendo \textbf{mesmos princípios de desenho}: definição a priori de janelas, quantificação de exposição (intensidade/duração), modelagem de \emph{impulso-resposta} e relato padronizado de efeitos.
\end{justify}

\begin{justify}
Na cultura celular/biologia molecular, identificam-se \emph{marcadores de estado} e vias. Na PCS, propomos um \textbf{marcador linguístico-cognitivo de estado} (AG5/KEC) com ancoragem funcional (ZuCo: custo de leitura/EEG). A exploração HELIO permanece \emph{covariável exógena} para deslocar o sistema entre regimes de maior/menor organização simbólica, sem alegar causalidade clínica individual.
\end{justify}

---

## 3. Formalismo mínimo (mapa causal executável)

\begin{align}
\mathcal{U}(t) &= \{{Kp, Dst, AE, B_z, V, N_p, P_{{dyn}}, F10.7}\}\\
\theta(t) &= f(\mathcal{U}(t), \text{{lags}}, \mathbf{{X_{{ctrl}}}}); \quad \mathbf{{X_{{ctrl}}}}=\{{\text{{sazonal}}, \text{{tópico}}, \text{{idioma}}, \text{{latitude}}}\}\\
Y(t) &= \{{\hat{{H}}}(t), \tilde{{\kappa}}(t), \mathrm{{Coh}}(t)\}\\
\text{{Aims}}: &\ \text{{SEA}}(\Delta Y|\text{{evento}}),\ \text{{VAR/ARIMAX}}(\mathcal{U}\to Y),\ \text{{ZuCo}}(\text{{AG5}}\to \text{{custo}})
\end{align}

\begin{justify}
Hipótese conservadora: perturbações geomagnéticas elevam \(\sigma(t)\) e/ou reduzem \(\beta(t)\) → aumento de \(\hat{H}\), redução de \(\tilde{\kappa}\) → queda do escore composto KEC/AG5. Direções e magnitudes são estimadas com IC e FDR, não postuladas a priori.
\end{justify}

---

## 4. Delineamentos (epidemiologia computacional-simbólica)

\begin{justify}
\textbf{SEA (Superposed Epoch Analysis)}: janelas fixas −3…+3 dias ao redor de eventos (Kp≥5; Dst≤−50/−100 nT), baseline por “dias calmos”, \emph{controls} sazonais/temáticos, \emph{placebos} (lags implausíveis) e \emph{ablation} (shuffle/grafo nulo).
\end{justify}

\begin{justify}
\textbf{Dinâmica (ARIMAX/VAR Bayes)}: impulsos de \(\mathcal{U}(t)\) quantilizada, IRFs com \emph{bootstrap}, hierarquias por idioma/latitude. Reporte padronizado: coeficientes, efeitos padronizados, IC, FDR.
\end{justify}

\begin{justify}
\textbf{Validação neurocognitiva (ZuCo)}: regressões mistas de \emph{custo de leitura} \(\sim\) AG5 local; confirma que a métrica capta organização informacional independentemente de HELIO (prova de mecanismo da métrica).
\end{justify}

---

## 5. Variáveis e operacionalização (data dictionary mínimo)

- **Exposição \(\mathcal{U}(t)\)**: Kp (3h), Dst (1h/diário), AE (min/h), \(B_z\) (min/h), \(V\) (min/h), \(N_p\), \(P_{{dyn}}\), F10.7 (diário).
- **Resposta \(Y(t)\)**: \(\hat{H}\) (entropia de transição), \(\tilde{\kappa}\) (curvatura Forman/Ollivier), \(\mathrm{Coh}\) (coerência local), escore KEC/AG5.
- **Controles \(\mathbf{{X_{{ctrl}}}}\)**: sazonalidade, dia da semana, idioma, “topic mix” (quando disponível), latitude aproximada do corpus.
- **Unidade de análise**: título/notícia (texto curto, timestamp) e séries agregadas por idioma; sessões ZuCo (sentença).

---

## 6. Critérios de inferência e falsificação

\begin{justify}
Adotamos \textbf{pré-registro leve} (janelas/eventos), correção por múltiplos testes (FDR), IC por \emph{bootstrap}, e três camadas de falsificação: (i) lags implausíveis; (ii) embaralhamento de trajetórias; (iii) grafos nulos preservando grau. Reportamos negativos e limites.
\end{justify}

---

## 7. Pontes clínicas (estado, não diagnóstico)

\begin{justify}
AG5/KEC é \textbf{marcador dimensional de estado} (RDoC: Sistemas Cognitivos/Processamento de Linguagem). Protocolos de 5–10 min (fala/leitura) podem ser usados como \emph{monitor de estado} em ambulatórios; HELIO entra como covariável ambiental exploratória, nunca como “causa” clínica individual.
\end{justify}

---

## 8. Alinhamento PPGBMR/PUC‑SP (Marli & Moema)

\begin{justify}
(\textbf{{Marli}}) Exportamos o rigor \emph{{exposição→resposta}} e a narrativa QbD para o domínio simbólico; entregamos método, toolbox e relatório padrão de efeitos — sem demandar dados de bancada.
\end{justify}

\begin{justify}
(\textbf{{Moema}}) Estabelecemos marcador linguístico com ancoragem funcional (ZuCo) que pode, em projetos futuros, correlacionar-se a biomarcadores celulares sob calendário controlado por eventos HELIO — sem uso na dissertação.
\end{justify}

---

## 9. Ética, legal e reprodutibilidade

\begin{justify}
Somente dados públicos; sem PII; \emph{{fetch}} documentado (proveniência); scripts, \emph{{seeds}}, versões \emph{{pinned}}, DOIs (Zenodo); licenças MIT (código) e CC BY (derivados). Transparência sobre incertezas e tamanhos de efeito esperados (pequenos/modestos).
\end{justify}

---

## 10. Frase‑âncora

\begin{justify}
\textbf{{PCS‑HELIO}} transforma variáveis heliogeofísicas oficiais em \emph{{drivers exógenos}} para uma \emph{{métrica objetiva de estado da organização do pensamento}}. É um desenho \emph{{exposição→resposta}} reprodutível, clinicamente audível e alinhado ao PPGBMR.
\end{justify}
