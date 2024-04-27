import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Tween, Easing, update as updateTween } from 'https://cdn.skypack.dev/@tweenjs/tween.js';


export default class ChatbotScene {
  constructor(parentEl) {
    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    parentEl.appendChild(this.renderer.domElement);

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x404040); // Soft white light
    this.scene.add(ambientLight);

    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(1, 1, 1); // Position the light
    this.scene.add(directionalLight);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;

    this.camera.position.set(-0.32, 0.39, 12.19);

    //this.initDynamicTexturePlane();
  }

  initDynamicTexturePlane() {
    const geometry = new THREE.PlaneGeometry(10, 10);
    const material = new THREE.MeshBasicMaterial({ opacity: 0, transparent: true });
    this.texturePlane = new THREE.Mesh(geometry, material);
    this.scene.add(this.texturePlane);
    this.texturePlane.position.z = -5;
  }

  setPlaneTexture(x,y,z,scale,opacity){
    // Reset plane properties
    this.texturePlane.scale.set(scale, scale, scale);
    this.texturePlane.material.opacity = opacity;
    this.texturePlane.position.set(x,y,z)
  }

  /*
  updatePlaneTexture(base64Image) {
    if (this.texturePlane.material.map) {
      // Dispose of the current texture
      this.texturePlane.material.map.dispose();
    }

    const loader = new THREE.TextureLoader();
    loader.load(
        base64Image, // the base64 image string
        function (texture) {
            // This function is called when the texture is loaded
            this.texturePlane.material.map = texture;
            this.texturePlane.material.needsUpdate = true;
    
            // Reset plane properties
            this.texturePlane.scale.set(1, 1, 1);
            this.texturePlane.material.opacity = 1;
    
            // Start animations after texture is loaded to ensure it doesn't start before setting the texture
            this.startAnimations();
        }.bind(this), // bind 'this' to maintain context
        undefined, // onProgress callback, not needed here
        function (error) {
            console.error('An error happened during loading the texture:', error);
        }
    );
    
  }

  startAnimations() {
    // Animate scale and opacity
    new Tween(this.texturePlane.scale)
        .to({ x: 2, y: 2 }, 40000)
        .easing(Easing.Exponential.Out)
        .start();

    new Tween(this.texturePlane.material)
        .to({ opacity: 0 }, 40000)
        .easing(Easing.Exponential.Out)
        .start();
  }
  */

  updatePlaneTexture(base64Image) {
    var imgContainer = document.getElementById('imageContainer');
    imgContainer.style.backgroundImage = 'url(' + base64Image + ')';

    // Continue with any other adjustments needed for the div
  }

  animate() {    
    this.controls.update();
    updateTween();  // Updated to use the `update` function correctly
    this.renderer.render(this.scene, this.camera);
  }  

  setCameraPos(x,y,z){
    this.camera.position.x = x;
    this.camera.position.y = y;
    this.camera.position.z = z;
  }

  getCameraPos(){
    return {"x":this.camera.position.x, "y":this.camera.position.y, "z":this.camera.position.z};
  }

  getScene() {
    return this.scene;
  }

  getCamera() {
    return this.camera;
  }

  getRenderer(){
    return this.renderer;
  }

  getControls(){
    return this.controls;
  }
}