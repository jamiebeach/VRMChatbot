import * as THREE from 'three';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { mixamoVRMRigMap } from './mixamoVRMRigMap.js';
import { VRMRigMap } from './VRMRigMap.js';

/**
 * Load Mixamo animation, convert for three-vrm use, and return it.
 *
 * @param {string} url A url of mixamo animation data
 * @param {VRM} vrm A target VRM
 * @returns {Promise<THREE.AnimationClip>} The converted AnimationClip
 */
export function loadMixamoAnimation( url, vrm ) {

	const loader = new FBXLoader(); // A loader which loads FBX
	console.log(url);
	return loader.loadAsync( url ).then( ( asset ) => {
		console.log(asset.animations);
		let clip = THREE.AnimationClip.findByName( asset.animations, 'mixamo.com' ); // extract the AnimationClip
		if(clip == null)
			clip = asset.animations[0];			

		const tracks = []; // KeyframeTracks compatible with VRM will be added here

		const restRotationInverse = new THREE.Quaternion();
		const parentRestWorldRotation = new THREE.Quaternion();
		const _quatA = new THREE.Quaternion();
		const _vec3 = new THREE.Vector3();

		//check if mixamo rig
		let testbone = asset.getObjectByName('mixamorigHips');
		let mixamo = true;
		if(!testbone){
			//Then this isn't based on a mixamo rig
			mixamo = false;
		}
		
		// Adjust with reference to hips height.
		let hipbone = (mixamo)?asset.getObjectByName( 'mixamorigHips' ):asset.getObjectByName( 'J_Bip_C_Hips' );
		let motionHipsHeight = hipbone.position.y;
		
		const vrmHipsY = vrm.humanoid?.getNormalizedBoneNode( 'hips' ).getWorldPosition( _vec3 ).y;
		const scene = (vrm.scene)?vrm.scene:vrm;
		const vrmRootY = scene.getWorldPosition( _vec3 ).y;
		const vrmHipsHeight = Math.abs( vrmHipsY - vrmRootY );
		const hipsPositionScale = vrmHipsHeight / motionHipsHeight;

		clip.tracks.forEach( ( track ) => {

			// Convert each tracks for VRM use, and push to `tracks`
			const trackSplitted = track.name.split( '.' );
			const mixamoRigName = trackSplitted[ 0 ];
			const vrmBoneName = (mixamo)?mixamoVRMRigMap[ mixamoRigName ]:VRMRigMap[mixamoRigName];
			const vrmNodeName = vrm.humanoid?.getNormalizedBoneNode( vrmBoneName )?.name;
			const mixamoRigNode = asset.getObjectByName( mixamoRigName );

			if ( vrmNodeName != null ) {

				const propertyName = trackSplitted[ 1 ];

				// Store rotations of rest-pose.
				mixamoRigNode.getWorldQuaternion( restRotationInverse ).invert();
				mixamoRigNode.parent.getWorldQuaternion( parentRestWorldRotation );

				if ( track instanceof THREE.QuaternionKeyframeTrack ) {

					// Retarget rotation of mixamoRig to NormalizedBone.
					for ( let i = 0; i < track.values.length; i += 4 ) {

						const flatQuaternion = track.values.slice( i, i + 4 );

						_quatA.fromArray( flatQuaternion );

						// 親のレスト時ワールド回転 * トラックの回転 * レスト時ワールド回転の逆
						_quatA
							.premultiply( parentRestWorldRotation )
							.multiply( restRotationInverse );

						_quatA.toArray( flatQuaternion );

						flatQuaternion.forEach( ( v, index ) => {

							track.values[ index + i ] = v;

						} );

					}

					tracks.push(
						new THREE.QuaternionKeyframeTrack(
							`${vrmNodeName}.${propertyName}`,
							track.times,
							track.values.map( ( v, i ) => ( vrm.meta?.metaVersion === '0' && i % 2 === 0 ? - v : v ) ),
						),
					);

				} else if ( track instanceof THREE.VectorKeyframeTrack ) {

					const value = track.values.map( ( v, i ) => ( vrm.meta?.metaVersion === '0' && i % 3 !== 1 ? - v : v ) * hipsPositionScale );
					tracks.push( new THREE.VectorKeyframeTrack( `${vrmNodeName}.${propertyName}`, track.times, value ) );

				}

			}

		} );

		return new THREE.AnimationClip( 'vrmAnimation', clip.duration, tracks );

	} );

}
