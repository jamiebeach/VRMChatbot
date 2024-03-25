
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
        this.isTalking=false; 

        this.nextViseme = '';
        this.lastViseme = '';
    }

    handleExpressions(onDoneTalking=undefined){
        var d = new Date();
        var curt = d.getTime();
        if(this.lastExpressionTime==0)
            this.lastExpressionTime = curt;
        const elapsedTime = curt - this.lastExpressionTime;
        this.lastExpressionTime = curt;

        this.blink(elapsedTime);

        //handle talking
        //this.handleTalking(elapsedTime, onDoneTalking);

        this.handleViseme();
    }

    updateViseme(newViseme){
      this.nextViseme = newViseme;
    }

    handleViseme(){
      if(this.nextViseme != this.lastViseme){
        //new viseme set, so change mouth accordingly.

      }
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

    changeMouthPhonemeStrength(ph, st){
      this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('ee' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('ih' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('oh' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('ou' , 0.0 );

      this.model.getCurrentVrm().expressionManager.setValue(ph, st );
    }

    changeMouthTo(viseme){

      /*
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
      */

      this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('ee' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('ih' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('oh' , 0.0 );
      this.model.getCurrentVrm().expressionManager.setValue('ou' , 0.0 );

      if(viseme == 'A'){
        this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.7 );
      }else if(viseme == 'B'){
        this.model.getCurrentVrm().expressionManager.setValue('ee' , 0.5 );
      }else if(viseme == 'C'){
        this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.3 );
      }else if(viseme == 'D'){
        this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.3 );
      }else if(viseme =='E'){
        this.model.getCurrentVrm().expressionManager.setValue('ou' , 0.5 );
        this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.3 );
      }else if(viseme == 'F'){
        this.model.getCurrentVrm().expressionManager.setValue('ou' , 0.6 );
      }else if(viseme == 'G'){
        this.model.getCurrentVrm().expressionManager.setValue('ou' , 0.6 );
        this.model.getCurrentVrm().expressionManager.setValue('ee' , 0.6 );
      }else if(viseme == 'H'){
        this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.6 );
      }else if(viseme == 'X'){
        this.model.getCurrentVrm().expressionManager.setValue('aa' , 0.0 );
      }
    }

    handleTalking(elapsedTime, onDoneTalking=undefined){
      if(this.currentPhoneme != '' || this.lastPhoneme != ''){
        this.talkTime += elapsedTime;
        const morphAmount = Math.abs(Math.sin(Math.PI * (this.talkTime/120)/2));
        //console.log(this.currentPhoneme + ', ' + morphAmount + ',' + this.talkTime);
        if(this.currentPhoneme != '')
          this.model.getCurrentVrm().expressionManager.setValue( this.currentPhoneme, morphAmount );

        if(this.lastPhoneme != '' && this.lastPhoneme != this.currentPhoneme)
          this.model.getCurrentVrm().expressionManager.setValue( this.lastPhoneme, 1 - morphAmount ); 

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
          this.isTalking = true;
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
        }else {
          if(this.isTalking){
            if(this.model.talk.queuelength() == 0){
              this.isTalking = false;
              if(onDoneTalking){
                onDoneTalking();
              }
            }
          }
        }
        this.currentPhoneme = v;
      }
    }
}