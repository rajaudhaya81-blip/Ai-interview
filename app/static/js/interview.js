// Interview Room Orchestrator - InterviewAI

let mediaRecorder;
let audioChunks = [];
let audioBlob;
let recognition;
let isRecordingInstance = false;

// Audio analytics
let voiceStartTime;
let totalVoiceDuration = 0; // seconds
let silenceThreshold = 2000; // ms to classify as hesitation pause
let lastWordTime = 0;
let hesitationPauses = 0;

// Follow-up state
let inFollowUpMode = false;

document.addEventListener('DOMContentLoaded', () => {
    const timerElement = document.getElementById('timer');
    const progressBar = document.getElementById('progress-bar');
    const startRecordBtn = document.getElementById('btn-record-start');
    const stopRecordBtn = document.getElementById('btn-record-stop');
    const submitBtn = document.getElementById('btn-submit');
    const textAnswer = document.getElementById('text-answer');
    const voiceAnswer = document.getElementById('voice-answer-container');
    const modeTextBtn = document.getElementById('btn-mode-text');
    const modeVoiceBtn = document.getElementById('btn-mode-voice');
    const audioPreview = document.getElementById('audio-preview');
    const fullscreenBtn = document.getElementById('btn-fullscreen');
    
    let timeRemaining = parseInt(timerElement.dataset.timeRemaining);
    const totalTime = parseInt(timerElement.dataset.timeLimit) * 60;
    const interviewId = timerElement.dataset.interviewId;

    // --- COUNTDOWN TIMER ---
    const timerInterval = setInterval(() => {
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            alert("Time's up! Submitting current progress.");
            autoSubmitInterview();
            return;
        }
        timeRemaining--;
        
        // Format time
        const mins = Math.floor(timeRemaining / 60);
        const secs = timeRemaining % 60;
        timerElement.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        // Progress bar percentage
        if (totalTime > 0) {
            const progressPct = ((totalTime - timeRemaining) / totalTime) * 100;
            progressBar.style.width = `${progressPct}%`;
        }

        // Visual warning when under 2 minutes
        if (timeRemaining < 120) {
            timerElement.classList.add('text-danger');
            timerElement.style.animation = 'bounce 1s infinite';
        }
    }, 1000);

    // --- FULLSCREEN LOGIC ---
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.log(`Error entering fullscreen: ${err.message}`);
                });
                fullscreenBtn.innerHTML = '<i class="bi bi-fullscreen-exit"></i> Exit Fullscreen';
            } else {
                document.exitFullscreen();
                fullscreenBtn.innerHTML = '<i class="bi bi-fullscreen"></i> Fullscreen';
            }
        });
    }

    // --- WEBCAM SIMULATION & STREAMING ---
    const video = document.getElementById('webcam-preview');
    const faceOverlay = document.getElementById('face-overlay');
    if (video) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(stream => {
                video.srcObject = stream;
                if (faceOverlay) faceOverlay.textContent = "Eye Contact & Attention Monitored (Simulated)";
            })
            .catch(err => {
                console.log("Webcam access denied or unavailable: ", err);
                if (faceOverlay) faceOverlay.innerHTML = "<span class='text-danger'>Camera Blocked (Voice-only active)</span>";
            });
    }

    // --- ANSWER MODE SWITCHER ---
    if (modeTextBtn && modeVoiceBtn) {
        modeTextBtn.addEventListener('click', () => {
            textAnswer.classList.remove('d-none');
            voiceAnswer.classList.add('d-none');
            modeTextBtn.classList.add('btn-primary-custom');
            modeTextBtn.classList.remove('btn-secondary-custom');
            modeVoiceBtn.classList.remove('btn-primary-custom');
            modeVoiceBtn.classList.add('btn-secondary-custom');
        });

        modeVoiceBtn.addEventListener('click', () => {
            textAnswer.classList.add('d-none');
            voiceAnswer.classList.remove('d-none');
            modeVoiceBtn.classList.add('btn-primary-custom');
            modeVoiceBtn.classList.remove('btn-secondary-custom');
            modeTextBtn.classList.remove('btn-primary-custom');
            modeTextBtn.classList.add('btn-secondary-custom');
            initSpeechRecognition();
        });
    }

    // --- SPEECH RECOGNITION (WEB SPEECH API) ---
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.log("Speech recognition not supported in this browser.");
            return;
        }
        
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            
            // Log timestamp for hesitation pauses
            const now = Date.now();
            if (lastWordTime > 0) {
                const diff = now - lastWordTime;
                if (diff > silenceThreshold) {
                    hesitationPauses++;
                    console.log(`Hesitation detected! Total: ${hesitationPauses}`);
                }
            }
            lastWordTime = now;

            // Append transcripts to the text area
            if (finalTranscript) {
                textAnswer.value += (textAnswer.value ? ' ' : '') + finalTranscript;
            }
        };

        recognition.onerror = (event) => {
            console.log("Speech recognition error: ", event.error);
        };
    }

    // --- AUDIO RECORDING (MICROPHONE CAPTURE) ---
    if (startRecordBtn && stopRecordBtn) {
        startRecordBtn.addEventListener('click', async () => {
            audioChunks = [];
            hesitationPauses = 0;
            lastWordTime = 0;
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audioPreview.src = audioUrl;
                    audioPreview.classList.remove('d-none');
                };

                mediaRecorder.start();
                if (recognition) {
                    recognition.start();
                }
                
                isRecordingInstance = true;
                voiceStartTime = Date.now();
                
                startRecordBtn.classList.add('d-none');
                stopRecordBtn.classList.remove('d-none');
                document.getElementById('recording-indicator').classList.remove('d-none');
                document.getElementById('avatar-orb').classList.add('speaking');
            } catch (err) {
                alert("Microphone permission denied. Please allow microphone access to practice speaking.");
            }
        });

        stopRecordBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            if (recognition) {
                recognition.stop();
            }
            
            isRecordingInstance = false;
            totalVoiceDuration += (Date.now() - voiceStartTime) / 1000;
            
            startRecordBtn.classList.remove('d-none');
            stopRecordBtn.classList.add('d-none');
            document.getElementById('recording-indicator').classList.add('d-none');
            document.getElementById('avatar-orb').classList.remove('speaking');
        });
    }

    // --- SUBMISSION FLOW & FOLLOW-UPS ---
    if (submitBtn) {
        submitBtn.addEventListener('click', async () => {
            const answerText = textAnswer.value.trim();
            if (!answerText) {
                alert("Please type or record an answer before submitting.");
                return;
            }

            // Disable buttons, show loading skeletons / indicator
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Evaluating...';
            document.getElementById('ai-typing-indicator').classList.remove('d-none');

            // 1. Upload audio if available
            let audioUrl = null;
            if (audioBlob) {
                const formData = new FormData();
                formData.append('audio', audioBlob);
                formData.append('interview_id', interviewId);
                formData.append('question_id', document.getElementById('current-question-id').value);
                
                try {
                    const uploadRes = await fetch('/interview/upload-audio', {
                        method: 'POST',
                        body: formData
                    });
                    const uploadData = await uploadRes.json();
                    if (uploadData.success) {
                        audioUrl = uploadData.audio_url;
                    }
                } catch (e) {
                    console.log("Audio upload failed: ", e);
                }
            }

            // Calculate words per minute (WPM)
            const wordCount = answerText.split(/\s+/).length;
            const wpm = totalVoiceDuration > 0 ? Math.round(wordCount / (totalVoiceDuration / 60)) : null;

            // Prepare submit payload
            const payload = {
                interview_id: interviewId,
                question_index: document.getElementById('current-question-index').value,
                answer_text: answerText,
                audio_url: audioUrl,
                wpm: wpm,
                pauses: hesitationPauses,
                remaining_time: timeRemaining
            };

            // Call appropriate endpoint depending on whether it's a follow-up response
            const endpoint = inFollowUpMode ? '/interview/submit-followup' : '/interview/submit-answer';
            if (inFollowUpMode) {
                payload.followup_answer_text = answerText;
            }

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Reset variables
                    audioBlob = null;
                    audioChunks = [];
                    if (audioPreview) {
                        audioPreview.src = '';
                        audioPreview.classList.add('d-none');
                    }
                    totalVoiceDuration = 0;

                    if (data.status === 'follow_up') {
                        // Enter follow-up state
                        inFollowUpMode = true;
                        
                        // Update UI to show follow-up prompt
                        document.getElementById('question-text-display').innerHTML = `
                            <p class="text-secondary small">Original Question: ${document.getElementById('question-text-display').textContent}</p>
                            <div class="alert alert-info border-info bg-dark-50 text-white">
                                <strong>Follow-up Question:</strong><br/> ${data.follow_up_question}
                            </div>
                        `;
                        textAnswer.value = '';
                        document.getElementById('input-label-mode').textContent = "Record/Type response to the follow-up question:";
                        
                        // Re-enable submit button
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Submit Follow-Up';
                    } else if (data.status === 'next') {
                        // Move to next question by reloading
                        window.location.reload();
                    } else if (data.status === 'completed') {
                        // Redirect to report
                        window.location.href = data.redirect_url;
                    }
                } else {
                    alert(`Error: ${data.message}`);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit Answer';
                }
            } catch (err) {
                console.log(err);
                alert("An error occurred during submission.");
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Answer';
            } finally {
                document.getElementById('ai-typing-indicator').classList.add('d-none');
            }
        });
    }

    // Pause functionality
    const pauseBtn = document.getElementById('btn-pause');
    if (pauseBtn) {
        pauseBtn.addEventListener('click', async () => {
            const isPaused = pauseBtn.classList.contains('paused');
            if (!isPaused) {
                // Pause session
                clearInterval(timerInterval);
                pauseBtn.classList.add('paused');
                pauseBtn.innerHTML = '<i class="bi bi-play-fill"></i> Resume Interview';
                
                await fetch('/interview/pause', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interview_id: interviewId, remaining_time: timeRemaining })
                });
                
                // Show modal overlay
                document.getElementById('paused-overlay').classList.remove('d-none');
            } else {
                // Resume session
                window.location.reload();
            }
        });
    }

    function autoSubmitInterview() {
        // Complete current interview session if timer runs out
        fetch('/interview/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                interview_id: interviewId,
                question_index: document.getElementById('current-question-index').value,
                answer_text: "Time expired. No response submitted.",
                remaining_time: 0
            })
        }).then(res => res.json()).then(data => {
            window.location.reload();
        });
    }
});
