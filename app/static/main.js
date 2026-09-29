// Echoes.ai phone page.
// Flow: pick an exhibit, hold the button and speak (or type), send the question
// to /ask, show the answer and its sources, then play the answer one piece at a
// time using /speak, fetching the next piece while the current one plays. If the
// answer comes with a sound (the T. rex can roar), it plays after the spoken
// lead-in, with a note from persona.json saying what the sound is.
//
// URL options: ?persona=t-rex picks the exhibit (use this in QR codes),
//              ?mode=neutral asks the plain museum guide instead (for demos),
//              ?session=P1 labels a user test in the server log, so that person's
//              questions can be exported with scripts/export_session_log.py.

(function () {
  "use strict";

  const params = new URLSearchParams(window.location.search);
  const mode = params.get("mode") === "neutral" ? "neutral" : "persona";
  const testLabel = (params.get("session") || "").trim();
  const isTest = /^[A-Za-z0-9_-]{1,32}$/.test(testLabel);
  const sessionId = isTest
    ? testLabel
    : (window.crypto && crypto.randomUUID)
      ? crypto.randomUUID()
      : String(Date.now()) + Math.random().toString(16).slice(2);

  const el = {
    exhibit: document.getElementById("exhibit"),
    greeting: document.getElementById("greeting"),
    period: document.getElementById("period"),
    talk: document.getElementById("talk"),
    talkLabel: document.getElementById("talk-label"),
    form: document.getElementById("text-form"),
    text: document.getElementById("text-question"),
    status: document.getElementById("status"),
    stop: document.getElementById("stop"),
    conversation: document.getElementById("conversation"),
    template: document.getElementById("turn-template"),
    sessionNote: document.getElementById("session-note"),
  };

  const STATUS_LABELS = {
    not_in_sources: "Not in my sources",
    outside_time: "Outside my time",
    declined: "Off topic",
  };

  let exhibits = [];
  let recorder = null;
  let chunks = [];
  let recordStart = 0;
  let holding = false;
  let busy = false;
  let audioContext = null;
  let currentSource = null;
  let playbackId = 0;
  const soundCache = new Map();

  // ------------------------------------------------------------ helpers

  function setStatus(message, isError) {
    el.status.textContent = message || "";
    el.status.classList.toggle("error", Boolean(isError));
  }

  function currentExhibit() {
    return exhibits.find(function (e) { return e.id === el.exhibit.value; });
  }

  function setBusy(value) {
    busy = value;
    el.talk.disabled = value;
    el.form.querySelector("button").disabled = value;
  }

  function safeUrl(url) {
    return /^https?:\/\//i.test(url || "") ? url : null;
  }

  // ------------------------------------------------------------ exhibits

  async function loadExhibits() {
    try {
      const response = await fetch("/personas");
      exhibits = await response.json();
    } catch (error) {
      setStatus("Could not load the exhibits. Is the server running?", true);
      return;
    }
    el.exhibit.innerHTML = "";
    exhibits.forEach(function (e) {
      const option = document.createElement("option");
      option.value = e.id;
      option.textContent = e.name;
      el.exhibit.appendChild(option);
    });
    const wanted = params.get("persona");
    if (wanted && exhibits.some(function (e) { return e.id === wanted; })) {
      el.exhibit.value = wanted;
    }
    showExhibit();
  }

  function showExhibit() {
    const e = currentExhibit();
    if (!e) {
      el.greeting.textContent = "No exhibits are set up yet.";
      return;
    }
    el.greeting.textContent = mode === "neutral"
      ? "Ask the museum guide anything about " + e.name + "."
      : e.greeting;
    el.period.textContent = e.name + ", " + e.time_period;
    el.talkLabel.textContent = "Hold to ask";
    el.conversation.innerHTML = "";
    setStatus("");
  }

  // ------------------------------------------------------------ audio playback

  function unlockAudio() {
    // Phones only allow sound after a tap, so we create and resume the audio
    // context during the first press of the button.
    if (!audioContext) {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (Context) audioContext = new Context();
    }
    if (audioContext && audioContext.state === "suspended") audioContext.resume();
  }

  function stopSpeaking() {
    playbackId += 1;
    if (currentSource) {
      try { currentSource.stop(); } catch (error) { /* already stopped */ }
      currentSource = null;
    }
    el.stop.hidden = true;
  }

  async function fetchClip(text) {
    const body = new FormData();
    body.append("persona", el.exhibit.value);
    body.append("text", text);
    const response = await fetch("/speak", { method: "POST", body: body });
    if (!response.ok) throw new Error("speech failed");
    const data = await response.arrayBuffer();
    return audioContext.decodeAudioData(data);
  }

  async function fetchSound(url) {
    if (!soundCache.has(url)) {
      const response = await fetch(url);
      if (!response.ok) throw new Error("sound failed");
      soundCache.set(url, await audioContext.decodeAudioData(await response.arrayBuffer()));
    }
    return soundCache.get(url);
  }

  function playBuffer(buffer, id) {
    return new Promise(function (resolve) {
      if (id !== playbackId) { resolve(); return; }
      const source = audioContext.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContext.destination);
      source.onended = function () { resolve(); };
      currentSource = source;
      source.start();
    });
  }

  async function speakSentences(sentences, onFirstAudio, soundUrl) {
    if (!audioContext || (!sentences.length && !soundUrl)) return;
    stopSpeaking();
    const id = playbackId;
    el.stop.hidden = false;
    try {
      let next = sentences.length ? fetchClip(sentences[0]) : null;
      const sound = soundUrl ? fetchSound(soundUrl) : null;
      for (let i = 0; i < sentences.length; i += 1) {
        const buffer = await next;
        if (id !== playbackId) return;
        next = i + 1 < sentences.length ? fetchClip(sentences[i + 1]) : null;
        if (i === 0 && onFirstAudio) onFirstAudio();
        await playBuffer(buffer, id);
      }
      if (sound) {
        const buffer = await sound;
        if (id !== playbackId) return;
        if (!sentences.length && onFirstAudio) onFirstAudio();
        await playBuffer(buffer, id);
      }
    } catch (error) {
      setStatus("The answer is shown above, but the voice could not be played.", true);
    } finally {
      if (id === playbackId) el.stop.hidden = true;
    }
  }

  // ------------------------------------------------------------ asking

  function addTurn(question) {
    const node = el.template.content.firstElementChild.cloneNode(true);
    node.querySelector(".question").textContent = question ? "You asked: " + question : "Listening...";
    el.conversation.appendChild(node);
    return node;
  }

  function showAnswer(node, data, askedAt) {
    node.querySelector(".question").textContent = "You asked: " + data.question;
    node.querySelector(".answer").textContent = data.answer;

    const badge = node.querySelector(".badge");
    if (STATUS_LABELS[data.status]) {
      badge.textContent = STATUS_LABELS[data.status];
      badge.hidden = false;
    }

    const sources = node.querySelector(".sources");
    const list = sources.querySelector("ul");
    (data.citations || []).forEach(function (c) {
      const item = document.createElement("li");
      const url = safeUrl(c.url);
      const name = document.createElement(url ? "a" : "span");
      name.textContent = c.source || c.id;
      if (url) {
        name.href = url;
        name.target = "_blank";
        name.rel = "noopener";
      }
      item.appendChild(name);
      if (c.licence) {
        const licence = document.createElement("span");
        licence.className = "licence";
        // "CC0 (The Metropolitan Museum of Art)" -> "CC0": the source name is already shown.
        licence.textContent = " (" + c.licence.split(" (")[0] + ")";
        item.appendChild(licence);
      }
      const snippet = document.createElement("span");
      snippet.className = "snippet";
      snippet.textContent = c.snippet ? '"' + c.snippet.trim() + '..."' : "";
      item.appendChild(snippet);
      list.appendChild(item);
    });
    if (list.children.length) {
      sources.querySelector("summary").textContent = "Sources (" + list.children.length + ")";
      sources.hidden = false;
    }

    if (data.sound && data.sound.note) {
      const note = document.createElement("p");
      note.className = "sound-note";
      note.textContent = "Sound: " + data.sound.note + ".";
      node.querySelector(".timing").before(note);
    }

    const seconds = ((performance.now() - askedAt) / 1000).toFixed(1);
    node.querySelector(".timing").textContent = "Answer shown after " + seconds + " s";
  }

  async function ask(fields) {
    if (busy) return;
    stopSpeaking();
    setBusy(true);
    setStatus("Thinking...");
    const askedAt = performance.now();
    const node = addTurn(fields.text || "");

    const body = new FormData();
    body.append("persona", el.exhibit.value);
    body.append("mode", mode);
    body.append("session_id", sessionId);
    if (fields.text) body.append("text", fields.text);
    if (fields.audio) body.append("audio", fields.audio, fields.filename);

    try {
      const response = await fetch("/ask", { method: "POST", body: body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Something went wrong.");
      showAnswer(node, data, askedAt);
      setStatus("");
      speakSentences(data.sentences || [], function () {
        const seconds = ((performance.now() - askedAt) / 1000).toFixed(1);
        const timing = node.querySelector(".timing");
        timing.textContent += ", voice started after " + seconds + " s";
      }, data.sound && data.sound.url);
    } catch (error) {
      node.remove();
      setStatus(error.message, true);
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------ recording

  function pickMimeType() {
    const options = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
    if (!window.MediaRecorder) return null;
    return options.find(function (type) { return MediaRecorder.isTypeSupported(type); }) || "";
  }

  async function startRecording() {
    if (busy || recorder) return;
    unlockAudio();
    stopSpeaking();
    if (window.isSecureContext === false) {
      setStatus("The microphone only works on a secure (https) link. Please type your question.", true);
      return;
    }
    const mimeType = pickMimeType();
    if (mimeType === null || !navigator.mediaDevices) {
      setStatus("This browser cannot record audio. Please type your question.", true);
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      setStatus("Microphone access was blocked. Allow it, or type your question.", true);
      return;
    }
    if (!holding) {
      // The button was released while the browser asked for microphone permission.
      stream.getTracks().forEach(function (track) { track.stop(); });
      setStatus("Microphone is ready. Now hold the button while you speak.");
      return;
    }
    chunks = [];
    recorder = mimeType ? new MediaRecorder(stream, { mimeType: mimeType }) : new MediaRecorder(stream);
    recorder.ondataavailable = function (event) { if (event.data.size) chunks.push(event.data); };
    recorder.onstop = function () {
      stream.getTracks().forEach(function (track) { track.stop(); });
      const type = recorder.mimeType || mimeType || "audio/webm";
      const heldFor = performance.now() - recordStart;
      recorder = null;
      el.talk.classList.remove("recording");
      el.talkLabel.textContent = "Hold to ask";
      if (heldFor < 500 || !chunks.length) {
        setStatus("Hold the button down while you speak.");
        return;
      }
      const extension = type.indexOf("mp4") !== -1 ? "mp4" : type.indexOf("ogg") !== -1 ? "ogg" : "webm";
      ask({ audio: new Blob(chunks, { type: type }), filename: "question." + extension });
    };
    recordStart = performance.now();
    recorder.start();
    el.talk.classList.add("recording");
    el.talkLabel.textContent = "Listening... let go to send";
    setStatus("");
  }

  function stopRecording() {
    holding = false;
    if (recorder && recorder.state === "recording") recorder.stop();
  }

  // ------------------------------------------------------------ events

  el.talk.addEventListener("pointerdown", function (event) {
    event.preventDefault();
    holding = true;
    // Keep receiving pointer events even if the finger slides off the button.
    if (el.talk.setPointerCapture) el.talk.setPointerCapture(event.pointerId);
    startRecording();
  });
  ["pointerup", "pointercancel"].forEach(function (name) {
    el.talk.addEventListener(name, stopRecording);
  });
  el.talk.addEventListener("keydown", function (event) {
    if ((event.key === " " || event.key === "Enter") && !event.repeat) {
      event.preventDefault();
      holding = true;
      startRecording();
    }
  });
  el.talk.addEventListener("keyup", function (event) {
    if (event.key === " " || event.key === "Enter") stopRecording();
  });
  el.talk.addEventListener("contextmenu", function (event) { event.preventDefault(); });

  el.form.addEventListener("submit", function (event) {
    event.preventDefault();
    const question = el.text.value.trim();
    if (!question) return;
    unlockAudio();
    el.text.value = "";
    ask({ text: question });
  });

  el.stop.addEventListener("click", stopSpeaking);
  el.exhibit.addEventListener("change", function () {
    stopSpeaking();
    showExhibit();
  });

  if (isTest && el.sessionNote) {
    el.sessionNote.textContent = "Test session " + testLabel;
    el.sessionNote.hidden = false;
  }
  loadExhibits();
})();
