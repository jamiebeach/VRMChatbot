export default class SocketHandler {
    constructor(onconnect, ondisconnect, onmessage){
        this.wsProtocol = window.location.protocol === 'https:' ? 'https' : 'http';
        this.socketUrl = `${this.wsProtocol}://${window.location.host}`;
        this.socket = io.connect(this.socketUrl, { transports: ['websocket'] });
        
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            if(onconnect){
                onconnect(this.socket);
            }            
        });        

        this.socket.on('disconnect', () => {
            if(ondisconnect){
                ondisconnect();
            }
            console.log('Disconnected from WebSocket server');
        });
        
        this.socket.on('message', (message) => {
            console.log(message);
            
            if(onmessage){
                onmessage(message);
            }
        });
    }

    interrupt(){
        this.socket.emit('interrupt');
    }

    messageSubmit(message){
        let t = (message[0] == '/')?'command':'text';
        let m = (message[0] == '/')?message.substring(1):message;
    
        var jsonMessage = {
            "type":t,
            "data":m
        };

        console.log(jsonMessage);
        this.socket.emit('message', JSON.stringify(jsonMessage));
    }   
    
    send(command, data){
        this.socket.emit(command, data);
    }

    getSocket(){
        return this.socket;
    }
}