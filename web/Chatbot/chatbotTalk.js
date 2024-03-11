import ChatbotModel from "./chatbotModel.js";
import {doubleMetaphone} from './double-metaphone.mjs'

export default class ChatbotTalk {
    constructor(cbModel){
        this.cbModel = cbModel;
        this.phonemeQueue = [];
    }

    process(sentence){
        const words = sentence.replace(/[^a-zA-Z ]/g, '').toLowerCase().split(' ');
        const phonemes = words.flatMap(word => doubleMetaphone(word)[0]);
        console.log(phonemes);

        phonemes.forEach(phneme => {
            phneme.split('').forEach(p => {
                this.phonemeQueue.push(p);
            });            
        });

        
    }

    getAndRemovePhoneme(phonemeArray) {
        if (phonemeArray.length === 0) {
          return null; // Return null if the array is empty
        }
      
        const phoneme = phonemeArray[0]; // Get the first element (oldest phoneme)
        phonemeArray.shift(); // Remove the first element from the array
      
        return phoneme;
    }

    getNextPhoneme(){
        if(this.phonemeQueue.length > 0){
            let p = this.getAndRemovePhoneme(this.phonemeQueue);
            return p;
        }else {
            return '';
        }
    }
}