
export default class ExpressionManager {
    constructor(model) {
        this.model = model;
        this.blinkTimer=0;
        this.isBlinking = false;
        this.nextBlinkTime=2500;
        this.expressionTime=0;
        this.lastExpressionTime=0;

        this.currentPhoneme='';
        this.lastPhoneme='';
        this.lastTalkTime=0;
        this.talkTime=0;
    }

    handleExpressions(){
        var d = new Date();
        var curt = d.getTime();
        if(this.lastExpressionTime==0)
            this.lastExpressionTime = curt;
        const elapsedTime = curt - this.lastExpressionTime;
        this.lastExpressionTime = curt;

        this.blink(elapsedTime);

        //handle talking
        this.handleTalking(elapsedTime);
    }

    blink(elapsedTime){
        this.blinkTimer += elapsedTime;
        if(!this.isBlinking && this.blinkTimer > this.nextBlinkTime){
          this.isBlinking = true;
          this.nextBlinkTime = 2500 + Math.random(2500);
          this.blinkTimer = 0;
        }

        if(this.isBlinking){
          const blinks = Math.sin( Math.PI * this.blinkTimer * 100);
          if(this.blinkTimer > 100){
            this.blinkTimer = 0;
            this.isBlinking = false;
            this.model.getCurrentVrm().expressionManager.setValue( 'blink', 0 );
          }else
            this.model.getCurrentVrm().expressionManager.setValue( 'blink', 0.5 - 0.5 * blinks );
        }
    }

    handleTalking(elapsedTime){
      if(this.currentPhoneme != '' || this.lastPhoneme != ''){
        this.talkTime += elapsedTime;
        const morphAmount = Math.abs(Math.sin(Math.PI * (this.talkTime/120)/2));
        console.log(this.currentPhoneme + ', ' + morphAmount + ',' + this.talkTime);
        if(this.currentPhoneme != '')
          this.model.getCurrentVrm().expressionManager.setValue( this.currentPhoneme, morphAmount );          this.model.getCurrentVrm().expressionManager.setValue( this.currentPhoneme, morphAmount );          

        if(this.lastPhoneme != '' && this.lastPhoneme != this.currentPhoneme)
          this.model.getCurrentVrm().expressionManager.setValue( this.lastPhoneme, 1 - morphAmount );          this.model.getCurrentVrm().expressionManager.setValue( this.currentPhoneme, morphAmount );          

        if(this.talkTime > 120){
          this.talkTime = 0;
          this.lastPhoneme = this.currentPhoneme;
          this.currentPhoneme = '';
        }
      }
      
      if(this.currentPhoneme == ''){
        var p = this.model.talk.getNextPhoneme();
        var v = '';
        if(p != ''){
          switch(p) {
            case 'A':
              v = 'aa';
            case 'E':
              v = 'ee';
            case 'I':
              v = 'ih';
            case 'O':
              v = 'oh';
            case 'U':
              v = 'ou';
            default:
              v = 'aa';
          }
        }
        this.currentPhoneme = v;
      }
    }
}