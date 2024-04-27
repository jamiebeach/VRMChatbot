export default class VoiceHelper {

    constructor(socket) {
        this.audioContext = null;
        this.audioBuffer = [];
        this.visemeData = [];
        this.visemeStartTime = 0; 
        this.voiceAnimationCallback = undefined;
        this.socket = socket;
        this.socket.binaryType = 'arraybuffer';
        this.animationLoopRunning = false;
        this.playingAudio = false;
        
        /*
        let domain = '{{domain}}';
        domain = domain.replace(/\/$/, '');
        let url = ('{{protocol}}'=='https')?'wss':'ws';
        let port = ('{{port}}'=='None')?'':':{{port}}';
        url = url + '://' + domain + port + '/audio_stream';
        //document.getElementById('output').innerHTML = url;
        */

        // Assuming your WebSocket server is running on the same domain and port
        /*
        var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        var ws_path = 'ws' + '://' + window.location.host;// + '/socket'; // Adjust the path accordingly
        console.log(ws_path);
        this.socket = undefined;

        try{
            //socket = new WebSocket(ws_path);
            console.log('about to connect ws to ' + window.location.protocol + '//' + window.location.host);
            this.socket = io.connect(window.location.protocol + '//' + window.location.host);
            console.log(this.socket);
        }catch(err){
            console.log('error establishing socket connection: ' + err);
        }

        //let socket = new WebSocket('ws://127.0.0.1:5000');
        this.socket.binaryType = 'arraybuffer'; // Make sure this line is present
        this.animationLoopRunning = false;

        this.socket.on('connect', function(event) {
            console.log('WebSocket is open now.');
            // Additional setup or initial messages to the server can be handled here
        });

*/
        this.socket.on('voice_message', async (event) => {
            console.log('in response');
            console.log('received ' + event.data);
            if (event.data === "END") {
                console.log('End of processing.');
                // Handle end of processing if needed
                return;
            }

            // Since we now send everything as JSON, we always parse the event.data.
            const messageJson = JSON.parse(event.data);

            // Check if the message is actually data (it will have audioBase64 and visemeData)
            if (messageJson.audioBase64 && messageJson.visemeData) {
                // Decode the base64 audio string to ArrayBuffer
                const audioArrayBuffer = await fetch(`data:audio/wav;base64,${messageJson.audioBase64}`).then(response => response.arrayBuffer());

                // Ensure the audio context is initialized
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }

                // Decode the ArrayBuffer into an AudioBuffer and push it to the audioBuffer array
                const audioChunk = await this.audioContext.decodeAudioData(audioArrayBuffer);
                this.audioBuffer.push(audioChunk);

                // Handle viseme data, which is unchanged
                this.visemeData.push(...messageJson.visemeData);
                if (!this.animationLoopRunning) {
                    this.playNextAudioBuffer(this.startVisemeSequence);
                }
            }
        });     

        /*
        this.socket.on('voice_message', async (event) => {
            console.log('in response');
            console.log('received ' + event.data);
            if (event.data === "END") {
                console.log('End of processing.');
                // Handle end of processing if needed
                return;
            } else if (typeof event.data === 'string') {
                // Handle viseme data
                const visemeJson = JSON.parse(event.data);
                this.visemeData.push(...visemeJson);
                if (!this.animationLoopRunning) {
                    this.playNextAudioBuffer(this.startVisemeSequence);
                    // Start the loop to display visemes
                    //setTimeout(() => playNextAudioBuffer(), 50);
                }
            } else {
                // This branch now properly handles ArrayBuffer data
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                console.log('decoding audio buffer...');
                const audioChunk = await this.audioContext.decodeAudioData(event.data);
                console.log('audiobuffer decoded.');
                this.audioBuffer.push(audioChunk);
                console.log('audiobufer.push success. audioBuffer.length=' + this.audioBuffer.length);
            }
        });
        */
        /*
        this.socket.onclose = function(event) {
            console.log('WebSocket is closed now.');
            animationLoopRunning = false;
        };
        */
    }

    end(){
        this.animationLoopRunning = false;
    }

    resetAudioContext(){
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    sendText(text, callback) {
        //const text = document.getElementById('textInput').value;
        /*
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(text);
        } else {
            console.log('WebSocket is not open. Cannot send text.');
        }
        */
        this.voiceAnimationCallback = callback;
        this.socket.emit('voice_message', text);
    }

    

    playNextAudioBuffer(onstart=undefined) {
        console.log('in playNextAudioBuffer');
        if (this.audioBuffer && this.audioBuffer.length > 0 && !this.playingAudio) {
            this.playingAudio = true;
            console.log('playing next audio buffer');
            console.log('audioBuffer.length = ' + this.audioBuffer.length);
            console.log('audioContext.state : ' + this.audioContext.state);

            const bufferToPlay = this.audioBuffer.shift();
            const source = this.audioContext.createBufferSource();
            source.buffer = bufferToPlay;
            source.connect(this.audioContext.destination);
            source.start(0);
            if(onstart)
                onstart(this);//setTimeout(()=>onstart(), 500);
            source.onended = ()=>{
                this.playingAudio = false;
                setTimeout(() => {
                    this.playNextAudioBuffer.bind(this)(onstart);
                }, 10);                
            };
        }else if(this.animationLoopRunning){
            console.log('setting timeout.');
            setTimeout(() => {
                if(this.visemeData.length > 0){
                    this.playNextAudioBuffer.bind(this)(onstart);
                }
            }, 10);
        }else{
            console.log('no longer playing audio bufffer');
        }
    }




    displayVisemes() {
        requestAnimationFrame(function updateVisemeDisplay(timestamp) {
            this.handleVisemes();
        });
    }

    startVisemeSequence(t) {
        let th = this;
        if(th == undefined)
            th = t;
        if (!th.animationLoopRunning) {
            th.animationLoopRunning = true;
            th.visemeStartTime = Date.now();
            //th.displayVisemes();
            requestAnimationFrame(function updateVisemeDisplay(timestamp) {
                th.handleVisemes(th);
            });
        }
    }

    handleVisemes(th){
        let _this = this;
        if(_this == undefined)
            _this = th;
        let n = Date.now();
        if(_this.visemeData.length > 0 && _this.visemeData[0].time == 0){
            _this.visemeStartTime = n;
        }
        let elapsedTime = (n - _this.visemeStartTime) / 1000;
        if (_this.visemeData.length > 0 && elapsedTime >= _this.visemeData[0].time) {
            let vd = _this.visemeData.shift();
            if(_this.voiceAnimationCallback){
                _this.voiceAnimationCallback(vd.viseme);
            }
            //document.getElementById('visemeDisplay').innerHTML = `<img src="/static/lisa-${vd.viseme}.png" alt="Viseme">`;
        }
        if (_this.animationLoopRunning) {
            if(_this.visemeData.length == 0){
                _this.animationLoopRunning = false;
            }
            requestAnimationFrame(function updateVisemeDisplay(timestamp) {
                _this.handleVisemes(_this);
            });        
        }            
    }

    getVisemes(){
        return this.visemeData;
    }
}