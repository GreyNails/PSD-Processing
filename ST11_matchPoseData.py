import json
import os

def parse_image_id(image_id):
    """
    Parse image_id to extract id, type, and z values
    Example: "0619_freepik_v2_01a1174a3a_2_12" -> 
    id: "0619_freepik_v2_01a1174a3a", type: 2, z: 12
    """
    # Remove the file extension if present
    base_id = image_id[0].replace('.png', '').replace('.jpg', '')
    
    # Split by underscore and reconstruct
    parts = base_id.split('_')
    
    # The last two parts are type and z
    z = int(parts[-1])
    type_value = int(parts[-2])
    
    # Everything before the last two parts is the id
    id_value = '_'.join(parts[:-2])
    
    return id_value, type_value, z

def find_pose_position(dataset_item, type_value, z_value):
    """
    Find the position (left, top, width, height) for a given type and z
    in the dataset item
    """
    # Find the index where both type and z match
    for i in range(len(dataset_item['z'])):
        if dataset_item['type'][i] == type_value and dataset_item['z'][i] == z_value:
            return {
                'left': dataset_item['left'][i],
                'top': dataset_item['top'][i],
                'width': dataset_item['width'][i],
                'height': dataset_item['height'][i],
                'z': z_value
            }
    return None

def merge_pose_and_dataset(pose_file='pose.json', dataset_file='dataset.json', output_file='merged_data.json'):
    """
    Main function to merge pose and dataset data
    """
    # Load JSON files
    with open(pose_file, 'r', encoding='utf-8') as f:
        pose_data = json.load(f)
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset_data = json.load(f)
    
    # Create a dictionary for quick dataset lookup by id
    dataset_dict = {item['id']: item for item in dataset_data}
    
    # Process each pose item
    merged_data = []
    
    for pose_item in pose_data:
        # Parse the image_id to get id, type, and z
        id_value, type_value, z_value = parse_image_id(pose_item['image_id'])
        
        # Find the corresponding dataset item
        if id_value in dataset_dict:
            dataset_item = dataset_dict[id_value]
            
            # Find the position for this pose
            pose_position = find_pose_position(dataset_item, type_value, z_value)
            
            if pose_position:
                # Get number of humans from detect_poses shape
                num_humans = len(pose_item['detect_poses'])
                
                # Create the merged item
                merged_item = {
                    "id": id_value,
                    "length": len(dataset_item['z']),  # Number of layers
                    "canvas_width": dataset_item['canvas_width'],
                    "canvas_height": dataset_item['canvas_height'],
                    "type": dataset_item['type'],
                    "left": dataset_item['left'],
                    "top": dataset_item['top'],
                    "width": dataset_item['width'],
                    "height": dataset_item['height'],
                    "z": dataset_item['z'],
                    "humanlayout": [
                        pose_position['left'],
                        pose_position['top'],
                        pose_position['width'],
                        pose_position['height'],
                        pose_position['z']
                    ],
                    "numberOfHuman": num_humans,
                    "body": pose_item['detect_poses'],
                    "cameraview": pose_item['detect_cameraView'],
                    "root": pose_item['global_orient']
                }
                
                merged_data.append(merged_item)
            else:
                print(f"Warning: Could not find position for pose {id_value} with type={type_value}, z={z_value}")
        else:
            print(f"Warning: Dataset not found for pose id: {id_value}")
    
    # Save the merged data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4, ensure_ascii=False)
    
    print(f"Merged data saved to {output_file}")
    print(f"Total merged items: {len(merged_data)}")
    
    return merged_data

def normalize_values(merged_data):
    """
    Optional: Normalize position values to [0, 1] range if needed
    """
    for item in merged_data:
        canvas_width = item['canvas_width']
        canvas_height = item['canvas_height']
        
        # Normalize arrays
        item['left'] = [l / canvas_width for l in item['left']]
        item['top'] = [t / canvas_height for t in item['top']]
        item['width'] = [w / canvas_width for w in item['width']]
        item['height'] = [h / canvas_height for h in item['height']]
        
        # Normalize humanlayout
        item['humanlayout'][0] /= canvas_width  # left
        item['humanlayout'][1] /= canvas_height  # top
        item['humanlayout'][2] /= canvas_width  # width
        item['humanlayout'][3] /= canvas_height  # height
    
    return merged_data

if __name__ == "__main__":
    # Run the merge process
    # input_data='/storage/human_psd/filltered_json/fillter_fpllz_v1.json'
    # input_pose='/storage/human_psd/pose_data/fpllz_v1/pose_data.json'
    # output_paht='/storage/crello_human_V2/V3/dataset/fpllz_v1.json'
    # output_paht_nor='/storage/crello_human_V2/V3/dataset/fpllz_v1_normalize.json'

    input_data='/storage/human_psd/filltered_json/fillter_fp_v2.json'
    input_pose='/storage/human_psd/pose_data/fp_v2/pose_data.json'
    output_paht='/storage/crello_human_V2/V3/dataset/fp_v2.json'
    output_paht_nor='/storage/crello_human_V2/V3/dataset/fp_v2_normalize.json'


    merged_data = merge_pose_and_dataset(input_pose,input_data,output_paht)

    merged_data = normalize_values(merged_data)


    
    # Optional: If you need normalized values (0-1 range) like in the example
    # Uncomment the following lines:
    # merged_data = normalize_values(merged_data)
    # with open('merged_data_normalized.json', 'w', encoding='utf-8') as f:
    #     json.dump(merged_data, f, indent=4, ensure_ascii=False)


    with open(output_paht_nor, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4, ensure_ascii=False)
    # Print a sample of the first merged item
    if merged_data:
        print("\nSample merged item:")
        print(json.dumps(merged_data[0], indent=2))


# Warning: Dataset not found for pose id: 0618_tao_llz_18f45b660d
# Warning: Dataset not found for pose id: 0618_tao_llz_3d0d9fec5f
# Warning: Dataset not found for pose id: 0618_tao_llz_b73c029a09
# Warning: Dataset not found for pose id: 0618_tao_llz_d1273f5a52
# Warning: Dataset not found for pose id: 0618_tao_llz_ff67d4e6e9