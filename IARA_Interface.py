from flask import Flask, jsonify, render_template_string
import serial
import json
import threading
import time
from datetime import datetime

# ==================================================
# CONFIGURAÇÃO DA SERIAL
# ==================================================

# Troque para a porta correta do seu ESP32.
# Exemplo: COM3, COM4, COM5...
PORTA_SERIAL = "COM3"
VELOCIDADE = 115200

app = Flask(__name__)

historico = []

dados_atuais = {
    "ph": "--",
    "temperatura": "--",
    "tensao_gpio": "--",
    "tensao_sensor": "--",
    "status": "Aguardando dados do ESP32",
    "cor": "#5DCAA5",
    "ultima_leitura": "--",
    "historico": []
}


def classificar_agua(ph, temperatura):
    try:
        ph = float(ph)
        temperatura = float(temperatura)

        if ph < 6.0:
            return "Água ácida", "#EF4444"
        elif ph > 8.5:
            return "Água alcalina", "#EF9F27"
        elif temperatura > 35:
            return "Temperatura elevada", "#EF9F27"
        else:
            return "Faixa aceitável", "#5DCAA5"

    except Exception:
        return "Aguardando dados", "#8A9A96"


def ler_serial():
    global dados_atuais, historico

    while True:
        try:
            with serial.Serial(PORTA_SERIAL, VELOCIDADE, timeout=2) as esp32:
                time.sleep(2)

                while True:
                    linha = esp32.readline().decode("utf-8", errors="ignore").strip()

                    if linha.startswith("{") and linha.endswith("}"):
                        dados = json.loads(linha)

                        ph = float(dados.get("ph", 0))
                        temperatura = float(dados.get("temperatura", 0))
                        tensao_gpio = float(dados.get("tensao_gpio", 0))
                        tensao_sensor = float(dados.get("tensao_sensor", 0))

                        status, cor = classificar_agua(ph, temperatura)

                        agora = datetime.now()
                        hora_completa = agora.strftime("%H:%M:%S")
                        hora_grafico = agora.strftime("%H:%M")

                        historico.append({
                            "hora": hora_grafico,
                            "ph": ph,
                            "temperatura": temperatura
                        })

                        historico = historico[-12:]

                        dados_atuais = {
                            "ph": f"{ph:.2f}",
                            "temperatura": f"{temperatura:.2f}",
                            "tensao_gpio": f"{tensao_gpio:.3f}",
                            "tensao_sensor": f"{tensao_sensor:.3f}",
                            "status": status,
                            "cor": cor,
                            "ultima_leitura": hora_completa,
                            "historico": historico
                        }

        except Exception as erro:
            dados_atuais = {
                "ph": "--",
                "temperatura": "--",
                "tensao_gpio": "--",
                "tensao_sensor": "--",
                "status": "Erro na Serial",
                "cor": "#EF4444",
                "ultima_leitura": "--",
                "historico": historico,
                "erro": str(erro)
            }

            time.sleep(3)


html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Projeto Iara</title>

  <style>
    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #F4F7F6;
      color: #04342C;
    }

    .navbar {
      height: 72px;
      background: white;
      border-bottom: 1px solid #E5E7EB;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 42px;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 20px;
      font-weight: 600;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      background: #BDEDDC;
      color: #04342C;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 23px;
    }

    .nav-links {
      display: flex;
      gap: 34px;
      color: #8A9A96;
      font-size: 15px;
    }

    .nav-links a {
      text-decoration: none;
      color: #8A9A96;
      transition: 0.2s;
    }

    .nav-links a:hover {
      color: #04342C;
    }

    .connection {
      background: #E1F5EE;
      color: #176B56;
      padding: 10px 16px;
      border-radius: 999px;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }

    .pulse {
      width: 9px;
      height: 9px;
      background: #2ECC71;
      border-radius: 50%;
      animation: pulse 1.3s infinite;
    }

    @keyframes pulse {
      0% {
        box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7);
      }

      70% {
        box-shadow: 0 0 0 9px rgba(46, 204, 113, 0);
      }

      100% {
        box-shadow: 0 0 0 0 rgba(46, 204, 113, 0);
      }
    }

    .hero {
      background: #04342C;
      color: white;
      text-align: center;
      padding: 90px 24px 100px;
    }

    .hero-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(93, 202, 165, 0.12);
      color: #5DCAA5;
      padding: 10px 16px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 26px;
    }

    .hero h1 {
      max-width: 850px;
      margin: 0 auto;
      font-size: 54px;
      line-height: 1.08;
      color: #BDEDDC;
      letter-spacing: -1.5px;
    }

    .hero p {
      max-width: 720px;
      margin: 24px auto 0;
      color: #A7D8C8;
      font-size: 18px;
      line-height: 1.7;
    }

    .hero-actions {
      margin-top: 34px;
      display: flex;
      justify-content: center;
      gap: 14px;
      flex-wrap: wrap;
    }

    .btn-primary,
    .btn-secondary {
      border-radius: 999px;
      padding: 14px 22px;
      font-weight: 700;
      font-size: 15px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 9px;
    }

    .btn-primary {
      background: #5DCAA5;
      color: #04342C;
    }

    .btn-secondary {
      background: transparent;
      color: #5DCAA5;
      border: 1px solid #5DCAA5;
    }

    .locations-section {
      background: #F4F7F6;
      padding: 42px 42px 18px;
    }

    .locations-inner {
      max-width: 1180px;
      margin: 0 auto;
    }

    .locations-header {
      text-align: center;
      margin-bottom: 24px;
    }

    .locations-header h2 {
      margin: 0;
      font-size: 32px;
      color: #04342C;
    }

    .locations-header p {
      margin: 10px auto 0;
      color: #6F817C;
      font-size: 15px;
      max-width: 720px;
      line-height: 1.6;
    }

    .locations-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    .location-card {
      border: 1px solid #DCE8E3;
      background: white;
      border-radius: 20px;
      padding: 20px;
      text-align: left;
      cursor: pointer;
      transition: 0.2s;
      color: #04342C;
      box-shadow: 0 8px 22px rgba(4, 52, 44, 0.04);
      font-family: inherit;
    }

    .location-card:hover {
      transform: translateY(-3px);
      border-color: #5DCAA5;
    }

    .location-card.active {
      border-color: #5DCAA5;
      background: #E1F5EE;
    }

    .location-card strong {
      display: block;
      font-size: 17px;
      margin: 10px 0 6px;
    }

    .location-card small {
      color: #6F817C;
      font-size: 13px;
    }

    .location-status {
      display: inline-block;
      width: 11px;
      height: 11px;
      border-radius: 50%;
    }

    .location-status.live {
      background: #2ECC71;
      box-shadow: 0 0 0 6px rgba(46, 204, 113, 0.15);
    }

    .location-status.planned {
      background: #EF9F27;
      box-shadow: 0 0 0 6px rgba(239, 159, 39, 0.15);
    }

    .selected-location {
      margin-top: 20px;
      background: white;
      border: 1px solid #E1E8E5;
      border-radius: 22px;
      padding: 24px;
      box-shadow: 0 8px 22px rgba(4, 52, 44, 0.04);
    }

    .selected-location h3 {
      margin: 0 0 8px;
      font-size: 24px;
      color: #04342C;
    }

    .selected-location p {
      margin: 0;
      color: #6F817C;
      line-height: 1.6;
    }

    .sensor-strip {
      padding: 34px 42px;
      background: #F4F7F6;
    }

    .sensor-grid {
      max-width: 1180px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    .metric-card {
      background: white;
      border: 1px solid #E1E8E5;
      border-radius: 22px;
      padding: 22px;
      box-shadow: 0 8px 22px rgba(4, 52, 44, 0.04);
    }

    .metric-label {
      color: #81918D;
      font-size: 14px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }

    .metric-value {
      font-size: 34px;
      font-weight: 800;
      color: #04342C;
      margin-bottom: 14px;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 11px;
      border-radius: 999px;
      background: #E1F5EE;
      color: #176B56;
      font-size: 13px;
      font-weight: 700;
    }

    .section {
      padding: 70px 42px;
    }

    .section-inner {
      max-width: 1180px;
      margin: 0 auto;
    }

    .section-title {
      font-size: 30px;
      margin: 0 0 24px;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #04342C;
    }

    .chart-card {
      background: white;
      border: 1px solid #E1E8E5;
      border-radius: 26px;
      padding: 28px;
      box-shadow: 0 8px 22px rgba(4, 52, 44, 0.04);
    }

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 26px;
    }

    .chart-subtitle {
      font-size: 18px;
      font-weight: 700;
      color: #04342C;
    }

    .tabs {
      display: flex;
      gap: 8px;
      background: #F2F6F4;
      padding: 5px;
      border-radius: 999px;
    }

    .tab {
      border: none;
      border-radius: 999px;
      padding: 8px 14px;
      cursor: pointer;
      font-weight: 700;
      color: #6F817C;
      background: transparent;
      font-family: inherit;
    }

    .tab.active {
      background: #E1F5EE;
      color: #176B56;
    }

    .bars {
      height: 230px;
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 12px;
      align-items: end;
      padding: 8px 0 14px;
      border-bottom: 1px solid #E5E7EB;
    }

    .bar-wrap {
      height: 100%;
      display: flex;
      align-items: end;
      justify-content: center;
    }

    .bar {
      width: 100%;
      max-width: 34px;
      min-height: 20px;
      border-radius: 999px 999px 8px 8px;
      background: #5DCAA5;
      transition: 0.3s;
    }

    .bar.warning {
      background: #EF9F27;
    }

    .labels {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 12px;
      margin-top: 10px;
      color: #879490;
      font-size: 12px;
      text-align: center;
    }

    .chart-note {
      margin-top: 18px;
      color: #7B8B86;
      font-size: 14px;
    }

    .why {
      background: #E1F5EE;
      text-align: center;
    }

    .why h2 {
      margin: 0;
      font-size: 34px;
      color: #04342C;
    }

    .why p {
      max-width: 780px;
      margin: 16px auto 38px;
      color: #176B56;
      font-size: 17px;
      line-height: 1.7;
    }

    .why-grid,
    .tech-grid {
      display: grid;
      gap: 18px;
    }

    .why-grid {
      grid-template-columns: repeat(3, 1fr);
    }

    .tech-grid {
      grid-template-columns: repeat(4, 1fr);
    }

    .why-card,
    .tech-card {
      background: white;
      border: 1px solid rgba(93, 202, 165, 0.35);
      border-radius: 24px;
      padding: 28px;
      text-align: left;
      box-shadow: 0 8px 22px rgba(4, 52, 44, 0.04);
    }

    .icon-large {
      font-size: 34px;
      margin-bottom: 16px;
      color: #176B56;
    }

    .why-card h3,
    .tech-card h3 {
      margin: 0 0 10px;
      color: #04342C;
      font-size: 20px;
    }

    .why-card p,
    .tech-card p {
      margin: 0;
      color: #667873;
      line-height: 1.6;
      font-size: 15px;
    }

    .footer {
      background: #04342C;
      color: #5DCAA5;
      padding: 32px 42px;
    }

    .footer-inner {
      max-width: 1180px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
    }

    .footer-brand {
      color: #BDEDDC;
      font-size: 20px;
      font-weight: 800;
      margin-bottom: 8px;
    }

    .footer-text {
      color: #5DCAA5;
      font-size: 14px;
    }

    .footer-links {
      display: flex;
      gap: 24px;
    }

    .footer-links a {
      color: #5DCAA5;
      text-decoration: none;
      font-size: 14px;
    }

    @media (max-width: 900px) {
      .navbar {
        padding: 0 20px;
      }

      .nav-links {
        display: none;
      }

      .hero h1 {
        font-size: 38px;
      }

      .sensor-grid,
      .locations-grid,
      .why-grid,
      .tech-grid {
        grid-template-columns: 1fr;
      }

      .chart-header,
      .footer-inner {
        flex-direction: column;
        align-items: flex-start;
      }

      .footer-links {
        flex-wrap: wrap;
      }

      .section,
      .sensor-strip,
      .locations-section {
        padding-left: 20px;
        padding-right: 20px;
      }
    }
  </style>
</head>

<body>
  <nav class="navbar">
    <div class="brand">
      <div class="brand-icon">💧</div>
      <span>Projeto Iara</span>
    </div>

    <div class="nav-links">
      <a href="#dados">Dados ao vivo</a>
      <a href="#sobre">Sobre</a>
      <a href="#contato">Contato</a>
    </div>

    <div class="connection">
      <span class="pulse" id="pulse"></span>
      <span id="conexao">ESP32 conectado</span>
    </div>
  </nav>

  <section class="hero">
    <div class="hero-pill">🌿 Monitoramento ambiental</div>
    <h1>Tecnologia a serviço da proteção dos corpos d'água</h1>
    <p>
      O Projeto Iara utiliza ESP32, sensor de pH e sensor de temperatura para acompanhar
      em tempo real indicadores importantes da qualidade da água, tornando o monitoramento
      ambiental mais acessível, visual e prático.
    </p>

    <div class="hero-actions">
      <a href="#dados" class="btn-primary">📈 Ver dados ao vivo</a>
      <a href="#sobre" class="btn-secondary">Conheça o projeto</a>
    </div>
  </section>

  <section class="locations-section">
    <div class="locations-inner">
      <div class="locations-header">
        <h2>Locais monitorados</h2>
        <p>
          Selecione um ponto de coleta para visualizar os dados ambientais. 
          O ponto ativo é onde o ESP32 está conectado no momento.
        </p>
      </div>

      <div class="locations-grid">
        <button class="location-card active" onclick="selecionarLocal('feira')" id="local-feira">
          <span class="location-status live"></span>
          <strong>Feira do InovaTech</strong>
          <small>Ponto ativo com ESP32</small>
        </button>

        <button class="location-card" onclick="selecionarLocal('mindu')" id="local-mindu">
          <span class="location-status planned"></span>
          <strong>Igarapé do Mindu</strong>
          <small>Monitoramento previsto</small>
        </button>

        <button class="location-card" onclick="selecionarLocal('rio-negro')" id="local-rio-negro">
          <span class="location-status planned"></span>
          <strong>Rio Negro</strong>
          <small>Monitoramento previsto</small>
        </button>

        <button class="location-card" onclick="selecionarLocal('distrito')" id="local-distrito">
          <span class="location-status planned"></span>
          <strong>Lago do Distrito Industrial</strong>
          <small>Monitoramento previsto</small>
        </button>
      </div>

      <div class="selected-location">
        <h3 id="nome-local">Feira do InovaTech</h3>
        <p id="descricao-local">
          Ponto de demonstração ativo do Projeto Iara. Os dados exibidos abaixo são coletados
          em tempo real pelo ESP32 conectado via USB Serial durante a Feira do InovaTech.
        </p>
      </div>
    </div>
  </section>

  <section class="sensor-strip" id="dados">
    <div class="sensor-grid">
      <div class="metric-card">
        <div class="metric-label">💧 pH da água</div>
        <div class="metric-value"><span id="ph">--</span> pH</div>
        <div class="status-pill">✅ <span id="status_ph">Aguardando</span></div>
      </div>

      <div class="metric-card">
        <div class="metric-label">🌡️ Temperatura</div>
        <div class="metric-value"><span id="temperatura">--</span> °C</div>
        <div class="status-pill">✅ <span id="status_temp">Normal</span></div>
      </div>

      <div class="metric-card">
        <div class="metric-label">🛡️ Status geral</div>
        <div class="metric-value" id="status_geral">--</div>
        <div class="status-pill">✅ Monitorando</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">⏱️ Última leitura</div>
        <div class="metric-value" id="ultima_leitura">--</div>
        <div class="status-pill">✅ Atualizado</div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">📈 Variação das últimas leituras</h2>

      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-subtitle" id="chart-title">pH monitorado</div>

          <div class="tabs">
            <button class="tab active" onclick="mudarGrafico('ph')" id="tab-ph">pH</button>
            <button class="tab" onclick="mudarGrafico('temperatura')" id="tab-temp">Temp.</button>
          </div>
        </div>

        <div class="bars" id="bars"></div>
        <div class="labels" id="labels"></div>

        <div class="chart-note" id="chart-note">
          Faixa ideal de pH para água doce: 6.5 a 8.5.
        </div>
      </div>
    </div>
  </section>

  <section class="section why" id="sobre">
    <div class="section-inner">
      <h2>Por que isso importa?</h2>
      <p>
        Pequenas alterações no pH e na temperatura podem indicar desequilíbrios ambientais,
        descarte irregular, contaminação ou condições desfavoráveis para a vida aquática.
        Monitorar esses dados ajuda a perceber riscos antes que se tornem problemas maiores.
      </p>

      <div class="why-grid">
        <div class="why-card">
          <div class="icon-large">⚠️</div>
          <h3>Detecção precoce</h3>
          <p>Ajuda a identificar mudanças anormais na água antes que o impacto ambiental se agrave.</p>
        </div>

        <div class="why-card">
          <div class="icon-large">🤝</div>
          <h3>Acesso comunitário</h3>
          <p>Permite que comunidades, estudantes e pesquisadores acompanhem dados ambientais de forma simples.</p>
        </div>

        <div class="why-card">
          <div class="icon-large">📚</div>
          <h3>Educação ambiental</h3>
          <p>Transforma dados técnicos em informação visual para apoiar conscientização e aprendizado.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-inner">
      <h2 class="section-title">🔌 Tecnologia embarcada</h2>

      <div class="tech-grid">
        <div class="tech-card">
          <div class="icon-large">🧠</div>
          <h3>ESP32</h3>
          <p>Microcontrolador responsável por receber os dados dos sensores e enviá-los ao sistema local.</p>
        </div>

        <div class="tech-card">
          <div class="icon-large">💧</div>
          <h3>Sensor de pH</h3>
          <p>Realiza a leitura aproximada da acidez ou alcalinidade da água monitorada.</p>
        </div>

        <div class="tech-card">
          <div class="icon-large">🌡️</div>
          <h3>Sensor de temperatura</h3>
          <p>Mede a temperatura da água, parâmetro importante para análise ambiental.</p>
        </div>

        <div class="tech-card">
          <div class="icon-large">🖥️</div>
          <h3>Interface localhost</h3>
          <p>Exibe os dados no navegador do computador por meio de comunicação USB Serial.</p>
        </div>
      </div>
    </div>
  </section>

  <footer class="footer" id="contato">
    <div class="footer-inner">
      <div>
        <div class="footer-brand">Projeto Iara</div>
        <div class="footer-text">Tecnologia a serviço da natureza — Manaus, AM</div>
      </div>

      <div class="footer-links">
        <a href="#">Dados abertos</a>
        <a href="#">GitHub</a>
        <a href="#">Contato</a>
      </div>
    </div>
  </footer>

  <script>
    let modoGrafico = "ph";
    let historicoAtual = [];
    let localAtivo = "feira";

    const locais = {
      feira: {
        nome: "Feira do InovaTech",
        descricao: "Ponto de demonstração ativo do Projeto Iara. Os dados exibidos abaixo são coletados em tempo real pelo ESP32 conectado via USB Serial durante a Feira do InovaTech.",
        ativo: true
      },
      mindu: {
        nome: "Igarapé do Mindu",
        descricao: "Ponto de monitoramento previsto. Ainda não há ESP32 instalado neste local, mas ele representa uma área urbana importante para acompanhamento ambiental.",
        ativo: false
      },
      "rio-negro": {
        nome: "Rio Negro",
        descricao: "Ponto de monitoramento previsto para acompanhamento da qualidade da água em uma das áreas de maior relevância ambiental da região amazônica.",
        ativo: false
      },
      distrito: {
        nome: "Lago do Distrito Industrial",
        descricao: "Ponto de monitoramento previsto para regiões com maior risco de descarte químico, resíduos industriais e alterações ambientais.",
        ativo: false
      }
    };

    function selecionarLocal(local) {
      localAtivo = local;

      document.querySelectorAll(".location-card").forEach(card => {
        card.classList.remove("active");
      });

      document.getElementById("local-" + local).classList.add("active");

      document.getElementById("nome-local").innerText = locais[local].nome;
      document.getElementById("descricao-local").innerText = locais[local].descricao;

      if (!locais[local].ativo) {
        document.getElementById("ph").innerText = "--";
        document.getElementById("temperatura").innerText = "--";
        document.getElementById("status_geral").innerText = "Sem sensor";
        document.getElementById("status_ph").innerText = "Aguardando instalação";
        document.getElementById("status_temp").innerText = "Sem leitura";
        document.getElementById("ultima_leitura").innerText = "--";
        document.getElementById("conexao").innerText = "Local sem ESP32";

        historicoAtual = [];
        renderizarGrafico();
      } else {
        document.getElementById("conexao").innerText = "ESP32 conectado";
        atualizarDados();
      }
    }

    function mudarGrafico(modo) {
      modoGrafico = modo;

      document.getElementById("tab-ph").classList.remove("active");
      document.getElementById("tab-temp").classList.remove("active");

      if (modo === "ph") {
        document.getElementById("tab-ph").classList.add("active");
        document.getElementById("chart-title").innerText = "pH monitorado";
        document.getElementById("chart-note").innerText = "Faixa ideal de pH para água doce: 6.5 a 8.5.";
      } else {
        document.getElementById("tab-temp").classList.add("active");
        document.getElementById("chart-title").innerText = "Temperatura monitorada";
        document.getElementById("chart-note").innerText = "A temperatura influencia diretamente a vida aquática e a oxigenação da água.";
      }

      renderizarGrafico();
    }

    function renderizarGrafico() {
      const bars = document.getElementById("bars");
      const labels = document.getElementById("labels");

      bars.innerHTML = "";
      labels.innerHTML = "";

      for (let i = 0; i < 12; i++) {
        const item = historicoAtual[i];

        let valor = 0;
        let hora = "--";

        if (item) {
          valor = modoGrafico === "ph" ? item.ph : item.temperatura;
          hora = item.hora;
        }

        let altura = 20;

        if (modoGrafico === "ph") {
          altura = Math.max(20, Math.min(210, (valor / 14) * 210));
        } else {
          altura = Math.max(20, Math.min(210, (valor / 45) * 210));
        }

        const foraPadrao = modoGrafico === "ph"
          ? (valor < 6.5 || valor > 8.5)
          : (valor > 35);

        const wrap = document.createElement("div");
        wrap.className = "bar-wrap";

        const bar = document.createElement("div");
        bar.className = foraPadrao && item ? "bar warning" : "bar";
        bar.style.height = altura + "px";

        wrap.appendChild(bar);
        bars.appendChild(wrap);

        const label = document.createElement("div");
        label.innerText = hora;
        labels.appendChild(label);
      }
    }

    function atualizarDados() {
      if (localAtivo !== "feira") {
        return;
      }

      fetch("/dados")
        .then(response => response.json())
        .then(data => {
          document.getElementById("ph").innerText = data.ph;
          document.getElementById("temperatura").innerText = data.temperatura;
          document.getElementById("status_geral").innerText = data.status;
          document.getElementById("status_ph").innerText = data.status;
          document.getElementById("ultima_leitura").innerText = data.ultima_leitura;

          if (data.temperatura !== "--") {
            document.getElementById("status_temp").innerText = "Normal";
          }

          document.getElementById("conexao").innerText = "ESP32 conectado";

          historicoAtual = data.historico || [];
          renderizarGrafico();
        })
        .catch(error => {
          document.getElementById("status_geral").innerText = "Erro";
          document.getElementById("conexao").innerText = "ESP32 desconectado";
        });
    }

    atualizarDados();
    setInterval(atualizarDados, 1000);
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(html)


@app.route("/dados")
def dados():
    return jsonify(dados_atuais)


if __name__ == "__main__":
    thread_serial = threading.Thread(target=ler_serial, daemon=True)
    thread_serial.start()

    app.run(host="127.0.0.1", port=5000, debug=False)