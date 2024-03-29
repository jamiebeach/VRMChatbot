import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export default class ChatbotScene {
  constructor(parentEl) {
    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
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

    this.camera.rotation.x=-5.57100671704551984;
    this.camera.rotation.y=-0.34286062223086816;
    this.camera.rotation.z=-0.05799141246354357;
    this.camera.position.x=-0.3199413950597789;
    this.camera.position.y=0.39321509045434044;
    this.camera.position.z=12.1874780998291223;

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