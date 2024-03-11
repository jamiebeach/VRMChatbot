import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';
import { animationUrls, happyAnimationUrls, idleAnimationsUrls } from './animationData.js';
import { loadMixamoAnimation } from './loadMixamoAnimation.js';
import ExpressionManager from './expressionManager.js';
import ChatbotTalk from './chatbotTalk.js';

export const STATES={
    'idle':'idle',
    'happy':'happy',
    'sad':'sad',
    'angry':'angry',
    'talking':'talking',
    'dancing':'dancing'
};

const ANIMATIONBASEURL = './Animations/';

export default class ChatbotModel {
    constructor(modelUrl, scene, onLoaded) {
        this.scene = scene;
        this.animationCache = new Map();
        this.currentMixer = undefined;
        this.currentVrm = undefined;
        this.currentAction = undefined;
        this.clock = new THREE.Clock();
        this.timet = 0;
        this.currentAnimationIndex = 0;
        this.currentAnimationUrl = '';
        this.params = {
            timeScale: 1.0,
        };
        this.expressionManager = undefined;
        this.state = STATES.idle;
        
        this.stateTimeout = 0;
        this.stateTimer = 0;

        this.idleTimer = 0;
        this.idleTimeout = 0;

        this.talk = new ChatbotTalk(this);

        this.preloaded = false;

        const loader = new GLTFLoader();
        // Install GLTFLoader plugin
        loader.register((parser) => {
            return new VRMLoaderPlugin(parser, {autoUpdateHumanBones: true});
        });

        loader.load(
            // URL of the VRM you want to load
            modelUrl,
        
            // called when the resource is loaded
            (gltf) => {
              // retrieve a VRM instance from gltf
              const vrm = gltf.userData.vrm;
              const vrmSceneObject = vrm.scene;
        
              // Rotate the VRM scene object by 180 degrees around the Y-axis
              //vrmSceneObject.rotation.y = Math.PI; // Math.PI is 180 degrees in radians
              vrmSceneObject.position.y = -1
              // add the loaded vrm to the scene
              this.currentVrm = vrm;
              scene.add(vrm.scene);
        
                    // Disable frustum culling
                    vrm.scene.traverse( ( obj ) => {
                obj.frustumCulled = false;  
              } );
        
              this.preloadAnimations().then(() => {
                this.preloaded = true;

                //if (currentAnimationUrl) {
                //  loadFBX(currentAnimationUrl);
                //}
                //setMood('relaxed');
                onLoaded();
              });    
        
              // Get the VRM model's animation mixer
              this.mixer = new THREE.AnimationMixer(vrm.scene);
        
              // Get the list of available animations
              const animations = gltf.animations;
        
              // Play the first animation (you can choose a specific animation if needed)
              console.log(animations);
        
              if(animations.length > 0){
                const action = mixer.clipAction(animations[0]);
                action.play();
              }
        
              this.expressionManager = new ExpressionManager(this);

              // deal with vrm features
              console.log(vrm);
              //animate(mixer);
            },
    
            (error) => this.log(error),
        );
    }

    log(error){
        //console.error(error)
    }

    getCurrentVrm() {
        return this.currentVrm;
    }

    getAnimationCache() {

    }

    preloadAnimations() {
        return Promise.all(animationUrls.map(async (url) => {
                if (!this.animationCache.has(url)) {
                const clip = await loadMixamoAnimation(ANIMATIONBASEURL + url, this.currentVrm);
                console.log('loaded ' + url);
                this.animationCache.set(url, clip);
            }
        }));
    }

    animate(){
        const deltaTime = this.clock.getDelta();
        this.timet += deltaTime;

        // If animation is loaded
        if (this.currentMixer) {
            // Update the animation
            this.currentMixer.update(deltaTime);
        }

        if (this.currentVrm) {
            this.currentVrm.update(deltaTime);

            if(this.state == STATES.idle){
                this.idle(deltaTime);
            }else {
                this.handleState(deltaTime);
            }
        }
        
        if(this.expressionManager){
            this.expressionManager.handleExpressions();
        }

        //For demo purposes
        //this.randomAnimations();

        //animateExpression();

    }

    loadFBX(animationUrl, transitionDuration=0.2) {
        // Create AnimationMixer for VRM
        const mixer = new THREE.AnimationMixer(this.currentVrm.scene);
      
        // Get the preloaded animation clip
        const clip = this.animationCache.get(animationUrl);
      
        if (clip) {
          // If there's a previously playing action, crossfade to the new action
          if (this.currentAction) {
            this.currentAction.crossFadeTo(mixer.clipAction(clip), transitionDuration, true);
          }
      
          // Apply the loaded animation to mixer and play
          this.currentAction = mixer.clipAction(clip);
          this.currentAction.play();
          this.currentMixer = mixer;
        } else {
          console.error(`Animation ${animationUrl} not found in cache.`);
        }
    }

    randomAnimations(){
        if (this.timet > 5) {
            this.timet = 0;
            console.log('updating animation');
            this.currentAnimationIndex++;
            if (this.currentAnimationIndex > animationUrls.length - 1) this.currentAnimationIndex = 0;
            this.currentAnimationUrl = animationUrls[this.currentAnimationIndex];
            this.loadFBX(this.currentAnimationUrl);
        }        
    }

    idle(deltaTime){
        this.idleTimer += deltaTime;
        if(this.idleTimer > this.idleTimeout){
            let idleAnimIndex = Math.floor((Math.random() * idleAnimationsUrls.length));
            console.log('updating idleAnimation to ' + idleAnimIndex);
            this.currentAnimationUrl = idleAnimationsUrls[idleAnimIndex];
            this.loadFBX(this.currentAnimationUrl, 2.5);
            this.idleTimer = 0;
            this.idleTimeout = Math.floor(3 + Math.random() * 5);
        }
    }

    handleState(deltaTime){
        this.stateTimer += deltaTime;
        if(this.stateTimer > this.stateTimeout){
            this.state = STATES.idle;
            this.stateTimer = 0;
            this.stateTimeout = 0;
        }
    }

    changeState(newState, durationS=5){
        let stateAnimation = '';
        this.state = newState;
        this.stateTimeout = durationS;

        if(newState == STATES.happy){
            const i = Math.floor((Math.random() * idleAnimationsUrls.length));
            this.currentAnimationUrl = happyAnimationUrls[i];
        }
        this.stateTimer = 0;
        this.loadFBX(this.currentAnimationUrl);
    }

    say(sentence, onResponse){
        fetch('/api/prompt', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: sentence })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response:', data.response);
            // Handle the response data as needed
            if(this.talk){
                this.talk.process(data.response);
            }
            if(onResponse)
                onResponse(data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            // Handle the error
        });

    }
}