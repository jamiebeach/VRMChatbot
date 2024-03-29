export default class VoiceHelper {

    constructor() {
        this.audioContext = null;
        this.audioBuffer = [];
        this.visemeData = [];
        this.visemeStartTime = 0; 
        this.voiceAnimationCallback = undefined;
        /*
        let domain = '{{domain}}';
        domain = domain.replace(/\/$/, '');
        let url = ('{{protocol}}'=='https')?'wss':'ws';
        let port = ('{{port}}'=='None')?'':':{{port}}';
        url = url + '://' + domain + port + '/audio_stream';
        //document.getElementById('output').innerHTML = url;
        */

        // Assuming your WebSocket server is running on the same domain and port
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


        this.socket.on('message', async (event) => {
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

        /*
        this.socket.onclose = function(event) {
            console.log('WebSocket is closed now.');
            animationLoopRunning = false;
        };
        */
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
        this.socket.emit('message', text);
    }

    playNextAudioBuffer(onstart=undefined) {
        console.log('in playNextAudioBuffer');
        if (this.audioBuffer && this.audioBuffer.length > 0) {
            console.log('playing next audio buffer');
            console.log('audioBuffer.length = ' + this.audioBuffer.length);
            const bufferToPlay = this.audioBuffer.shift();
            const source = this.audioContext.createBufferSource();
            source.buffer = bufferToPlay;
            source.connect(this.audioContext.destination);
            source.start(0);
            if(onstart)
                onstart(this);//setTimeout(()=>onstart(), 500);
            source.onended = ()=>{
                setTimeout(() => {
                    this.playNextAudioBuffer.bind(this)(onstart);
                }, 200);                
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