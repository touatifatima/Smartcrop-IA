# def explain_with_lime(features_df: pd.DataFrame, models: dict) -> Dict[str, Any]:
#     """
#     Generate LIME explanation for a prediction
    
#     Parameters:
#     -----------
#     features_df: DataFrame containing the features
#     models: Dictionary of loaded models
    
#     Returns:
#     --------
#     Dictionary with explanation data and visualization
#     """
#     if not hasattr(models['crop_model'], "predict_proba"):
#         return {"error": "Model does not support predict_proba, cannot use LIME"}
    
#     # Prepare data
#     X = models['column_transformer'].transform(features_df)
#     X_scaled = models['scaler'].transform(X)
    
#     # Get prediction
#     prediction = models['crop_model'].predict(X_scaled)[0]
#     predicted_class = models['label_encoder'].inverse_transform([prediction])[0]
    
#     # Create explainer
#     explainer = LimeTabularExplainer(
#         training_data=X_train,
#         feature_names=feature_names,
#         class_names=[str(cls) for cls in models['label_encoder'].classes_],
#         mode='classification'
#     )
    
#     # Generate explanation
#     explanation = explainer.explain_instance(
#         X_scaled[0], 
#         models['crop_model'].predict_proba, 
#         num_features=10
#     )
    
#     # Get explanation as list for the predicted class index
#     pred_idx = int(np.where(models['label_encoder'].classes_ == predicted_class)[0][0])
#     try:
#         exp_list = explanation.as_list(label=pred_idx)
#     except KeyError:
#         # Fallback to the first class if specific class explanation isn't available
#         available_labels = list(explanation.local_exp.keys())
#         if available_labels:
#             exp_list = explanation.as_list(label=available_labels[0])
#         else:
#             return {"error": "No explanations available."}
    
#     # Create DataFrame from explanation
#     exp_df = pd.DataFrame(exp_list, columns=['Feature', 'Impact'])
#     exp_df['Abs_Impact'] = exp_df['Impact'].abs()
#     exp_df = exp_df.sort_values('Abs_Impact', ascending=False)
    
#     # Map feature names to readable format
#     def get_feature_display_name(feature_str):
#         if "State_Name" in feature_str:
#             state = feature_str.split('_')[-1].replace('_', ' ').title()
#             return f"State: {state}"
        
#         if "Crop_Type" in feature_str:
#             crop_type = feature_str.split('_')[-1].title()
#             return f"Crop Type: {crop_type}"
        
#         feature_mapping = {
#             "N": "Nitrogen (N)",
#             "P": "Phosphorus (P)",
#             "K": "Potassium (K)",
#             "ph": "pH",
#             "rainfall": "Rainfall",
#             "temperature": "Temperature", 
#             "Humidity_calculated": "Humidity",
#             "Area_in_hectares": "Area (ha)",
#             "Production_in_tons": "Production (tons)",
#             "Yield_ton_per_hec": "Yield (t/ha)"
#         }
        
#         for key, value in feature_mapping.items():
#             if key in feature_str:
#                 return value
        
#         return feature_str
    
#     exp_df['Display_Name'] = exp_df['Feature'].apply(get_feature_display_name)
    
#     # Add current values
#     exp_df['Current_Value'] = np.nan
#     instance_to_explain = X_scaled[0]
#     for i, feature in enumerate(exp_df['Feature']):
#         for fname, idx in zip(feature_names, range(len(feature_names))):
#             if fname in feature:
#                 value = features_df.iloc[0].get(fname)
#                 if value is not None:
#                     exp_df.loc[i, 'Current_Value'] = round(float(value), 2)
#                 break
    
#     # Add impact direction
#     exp_df['Direction'] = 'Neutral'
#     exp_df.loc[exp_df['Impact'] > 0.05, 'Direction'] = 'Positive'
#     exp_df.loc[exp_df['Impact'] < -0.05, 'Direction'] = 'Negative'
    
#     # Generate advice based on feature importance
#     def get_advice_for_feature(feature_str, impact_value):
#         advices = []
        
#         if "N" in feature_str and not "State_Name" in feature_str:
#             if impact_value > 0:
#                 advices.append("Maintain nitrogen levels to optimize crop growth.")
#             else:
#                 advices.append("Consider reducing nitrogen fertilizer application.")
        
#         elif "P" in feature_str:
#             if impact_value > 0:
#                 advices.append("Current phosphorus levels are beneficial for this crop.")
#             else:
#                 advices.append("Consider adjusting phosphorus levels for better results.")
        
#         elif "K" in feature_str:
#             if impact_value > 0:
#                 advices.append("Maintain potassium levels to support crop health.")
#             else:
#                 advices.append("You may need to adjust potassium fertilization.")
        
#         elif "rainfall" in feature_str:
#             if impact_value > 0:
#                 advices.append("Current rainfall levels are good for this crop.")
#             else:
#                 advices.append("Consider irrigation solutions if rainfall is insufficient.")
        
#         elif "temperature" in feature_str:
#             if impact_value > 0:
#                 advices.append("The temperature range is suitable for this crop.")
#             else:
#                 advices.append("Temperature conditions may need management for this crop.")
        
#         elif "ph" in feature_str:
#             if impact_value > 0:
#                 advices.append("Maintain soil pH in the current range for best results.")
#             else:
#                 advices.append("Consider adjusting soil pH to optimize growing conditions.")
        
#         elif "Humidity_calculated" in feature_str:
#             if impact_value > 0:
#                 advices.append("Current humidity levels support crop growth.")
#             else:
#                 advices.append("Monitor humidity levels to prevent fungal diseases.")
        
#         if impact_value > 0:
#             advices.append("This parameter positively affects your crop yield.")
#         elif impact_value < 0:
#             advices.append("This parameter may negatively affect your crop yield.")
#         else:
#             advices.append("This parameter has minimal impact on your crop yield.")
        
#         return advices[0] if advices else "No specific advice available."
    
#     exp_df['Advice'] = exp_df.apply(lambda x: get_advice_for_feature(x['Feature'], x['Impact']), axis=1)
    
#     # Create visualization
#     plt.figure(figsize=(20, 16))
#     gs = plt.GridSpec(2, 2, height_ratios=[1, 1], width_ratios=[1.5, 1])
    
#     # ===== 1. Detailed Parameter Analysis Table =====
#     ax1 = plt.subplot(gs[0, 0])
#     ax1.axis('tight')
#     ax1.axis('off')
    
#     # Prepare table data
#     table_data = [
#         ['Parameter', 'Current Value', 'Impact', 'Score']
#     ]
    
#     for _, row in exp_df.head(10).iterrows():
#         # Format impact with arrow
#         if row['Direction'] == 'Positive':
#             impact = '↑\nPositive'
#             color = 'green'
#         elif row['Direction'] == 'Negative':
#             impact = '↓\nNegative'
#             color = 'red'
#         else:
#             impact = '—\nNeutral'
#             color = 'gray'
        
#         table_data.append([
#             row['Display_Name'],
#             str(row['Current_Value']),
#             impact,
#             f"{abs(row['Impact']):.2f}"
#         ])
    
#     # Create color mapping for rows
#     colors = []
#     for i in range(len(table_data)):
#         if i == 0:  # Header row
#             colors.append(['#e6fff2', '#e6fff2', '#e6fff2', '#e6fff2'])
#         else:
#             if 'Positive' in table_data[i][2]:
#                 row_color = '#f2f9e8'  # Light green for positive
#             elif 'Negative' in table_data[i][2]:
#                 row_color = '#f9e8e8'  # Light red for negative
#             else:
#                 row_color = '#f5f5f5'  # Light gray for neutral
#             colors.append([row_color, row_color, row_color, row_color])
    
#     # Create table
#     table = ax1.table(
#         cellText=table_data,
#         cellLoc='center',
#         loc='center',
#         colWidths=[0.3, 0.2, 0.2, 0.2],
#         cellColours=colors
#     )
    
#     # Customize table
#     table.auto_set_font_size(False)
#     table.set_fontsize(12)
#     for (i, j), cell in table.get_celld().items():
#         if i == 0:  # Header row
#             cell.set_text_props(weight='bold', color='darkgreen')
        
#         # Color the impact text
#         if j == 2 and i > 0:  # Impact column
#             if 'Positive' in table_data[i][j]:
#                 cell.get_text().set_color('green')
#             elif 'Negative' in table_data[i][j]:
#                 cell.get_text().set_color('red')
    
#     ax1.set_title('Detailed Parameter Analysis', fontsize=16, fontweight='bold', color='darkgreen', pad=20)
    
#     # ===== 2. Parameter Impact Bar Chart =====
#     ax2 = plt.subplot(gs[0, 1])
    
#     # Select top features by absolute impact
#     top_features = exp_df.sort_values('Abs_Impact', ascending=False).head(8)
    
#     # Get feature names and impact values
#     feature_names_display = top_features['Display_Name'].tolist()
#     impact_values = top_features['Impact'].tolist()
    
#     # Create color mapping for bars
#     bar_colors = ['#4CAF50' if impact > 0 else '#F44336' for impact in impact_values]
    
#     # Create bar chart
#     y_pos = np.arange(len(feature_names_display))
#     bars = ax2.barh(y_pos, impact_values, color=bar_colors, alpha=0.7)
    
#     # Add labels and customize
#     ax2.set_yticks(y_pos)
#     ax2.set_yticklabels(feature_names_display)
#     ax2.invert_yaxis()  # Display top-to-bottom
#     ax2.set_xlabel('Impact Score', fontsize=12)
#     ax2.set_title('Parameter Impact (LIME)', fontsize=16, fontweight='bold', color='darkgreen')
#     ax2.grid(axis='x', linestyle='--', alpha=0.7)
#     ax2.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    
#     # Add explanation text
#     ax2.text(0.5, -0.1, 'This chart shows how each parameter influences the recommendation.',
#              horizontalalignment='center', transform=ax2.transAxes, fontsize=10, style='italic')
    
#     # ===== 3. Farming Advice =====
#     ax3 = plt.subplot(gs[1, :])
#     ax3.axis('tight')
#     ax3.axis('off')
    
#     # Get top 3 most important features
#     top_features_advice = exp_df.sort_values('Abs_Impact', ascending=False).head(3)
    
#     # Prepare advice text
#     advice_title = f"Farming Advice for {predicted_class}"
#     advice_text = ""
    
#     for i, (_, row) in enumerate(top_features_advice.iterrows()):
#         feature_name = row['Display_Name']
#         advice = row['Advice']
        
#         advice_text += f"🌱 {advice}\n\n"
    
#     # Add general advice
#     advice_text += "🌱 Monitor field conditions regularly and adjust practices as needed.\n\n"
#     advice_text += "🌱 Consider crop rotation to maintain soil health and prevent pest buildup.\n"
    
#     # Display advice in a text box
#     props = dict(boxstyle='round', facecolor='#e6fff2', alpha=0.5)
#     ax3.text(0.5, 0.5, advice_text, transform=ax3.transAxes, fontsize=12,
#              verticalalignment='center', horizontalalignment='center', bbox=props, wrap=True)
    
#     ax3.set_title(advice_title, fontsize=16, fontweight='bold', color='darkgreen')
    
#     # Save the figure to a BytesIO object
#     buf = BytesIO()
#     plt.tight_layout()
#     plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
#     buf.seek(0)
    
#     # Convert the image to base64 string
#     img_str = base64.b64encode(buf.read()).decode('utf-8')
#     plt.close()
    
#     # Convert the explanation dataframe to a list of records
#     features_importance = exp_df[['Display_Name', 'Impact', 'Direction', 'Advice']].to_dict(orient='records')
    
#     return {
#         "predicted_crop": predicted_class,
#         "feature_importance": features_importance,
#         "advice": [row['Advice'] for _, row in top_features_advice.iterrows()],
#         "image": img_str
#     }


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from lime.lime_tabular import LimeTabularExplainer
from typing import Dict, Any, List
import json
import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lime.lime_tabular import LimeTabularExplainer
def explain_with_lime_api(

    features_df: pd.DataFrame,

    models: dict,

    X_train: np.ndarray,

) -> str:

    try:

        if not hasattr(models['crop_model'], "predict_proba"):

            return json.dumps({"error": "Model does not support predict_proba, cannot use LIME"})



        # Transform the input features

        X = models['column_transformer'].transform(features_df)

        X_scaled = models['scaler'].transform(X)



        # Convert sparse matrix to dense to avoid warnings

        if hasattr(X_scaled, 'toarray'):

            X_scaled = X_scaled.toarray()

        if hasattr(X, 'toarray'):

            X = X.toarray()



        # Make prediction

        prediction = models['crop_model'].predict(X_scaled)[0]

        predicted_class = models['label_encoder'].inverse_transform([prediction])[0]



        # Define the actual feature names after transformation

        feature_names = [

            'encoder__State_Name_andaman and nicobar islands', 'encoder__State_Name_andhra pradesh',

            'encoder__State_Name_arunachal pradesh', 'encoder__State_Name_assam', 'encoder__State_Name_bihar',

            'encoder__State_Name_chandigarh', 'encoder__State_Name_chhattisgarh', 'encoder__State_Name_dadra and nagar haveli',

            'encoder__State_Name_goa', 'encoder__State_Name_gujarat', 'encoder__State_Name_haryana',

            'encoder__State_Name_himachal pradesh', 'encoder__State_Name_jammu and kashmir', 'encoder__State_Name_jharkhand',

            'encoder__State_Name_karnataka', 'encoder__State_Name_kerala', 'encoder__State_Name_madhya pradesh',

            'encoder__State_Name_maharashtra', 'encoder__State_Name_manipur', 'encoder__State_Name_meghalaya',

            'encoder__State_Name_mizoram', 'encoder__State_Name_nagaland', 'encoder__State_Name_odisha',

            'encoder__State_Name_puducherry', 'encoder__State_Name_punjab', 'encoder__State_Name_rajasthan',

            'encoder__State_Name_sikkim', 'encoder__State_Name_tamil nadu', 'encoder__State_Name_telangana',

            'encoder__State_Name_tripura', 'encoder__State_Name_uttar pradesh', 'encoder__State_Name_uttarakhand',

            'encoder__State_Name_west bengal', 'encoder__Crop_Type_kharif', 'encoder__Crop_Type_rabi', 

            'encoder__Crop_Type_summer', 'encoder__Crop_Type_whole year', 'remainder__N', 'remainder__P', 

            'remainder__K', 'remainder__ph', 'remainder__rainfall', 'remainder__temperature', 'remainder__Area_in_hectares',

            'remainder__Production_in_tons', 'remainder__Yield_ton_per_hec', 'remainder__Humidity_calculated'

        ]



        # Debug prints

        print(f"X_train shape: {X_train.shape}")

        print(f"X_scaled shape: {X_scaled.shape}")

        print(f"Number of features: {X_scaled.shape[1]}")



        # Ensure we have the right number of feature names

        if len(feature_names) != X_scaled.shape[1]:

            print(f"Warning: Feature names count ({len(feature_names)}) doesn't match X_scaled features ({X_scaled.shape[1]})")

            # Adjust feature names to match the actual number of features

            if len(feature_names) > X_scaled.shape[1]:

                feature_names = feature_names[:X_scaled.shape[1]]

            else:

                # Add generic names for missing features

                while len(feature_names) < X_scaled.shape[1]:

                    feature_names.append(f'feature_{len(feature_names)}')



        # KEY FIX: Create proper training data with matching dimensions

        # The original X_train needs to be transformed through the same pipeline

        print(f"Original X_train shape: {X_train.shape}")

        

        # If X_train doesn't match the transformed feature space, we need to create synthetic training data

        if X_train.shape[1] != X_scaled.shape[1]:

            print(f"Feature mismatch: X_train has {X_train.shape[1]} features, X_scaled has {X_scaled.shape[1]}")

            

            # Create synthetic training data by generating variations around the current instance

            np.random.seed(42)

            n_samples = min(1000, X_train.shape[0])  # Limit samples for performance

            

            # Get the current instance

            current_instance = X_scaled[0]

            

            # Generate training data by adding noise to the current instance

            X_train_synthetic = []

            for _ in range(n_samples):

                # Add Gaussian noise with different scales for different features

                noise = np.random.normal(0, 0.1, size=current_instance.shape)

                # For binary features (likely 0 or 1), use smaller noise

                binary_mask = np.logical_or(np.abs(current_instance) < 0.1, 

                                          np.abs(current_instance - 1) < 0.1)

                noise[binary_mask] = np.random.normal(0, 0.00, size=np.sum(binary_mask))

                

                synthetic_sample = current_instance + noise

                X_train_synthetic.append(synthetic_sample)

            

            X_train_for_lime = np.array(X_train_synthetic)

            print(f"Created synthetic X_train with shape: {X_train_for_lime.shape}")

        else:

            # Use original training data but ensure it's properly scaled

            # Take a subset for performance

            n_samples = min(1000, X_train.shape[0])

            indices = np.random.choice(X_train.shape[0], n_samples, replace=False)

            X_train_for_lime = X_train[indices]

            

            # Ensure it's dense

            if hasattr(X_train_for_lime, 'toarray'):

                X_train_for_lime = X_train_for_lime.toarray()



        print(f"Final X_train_for_lime shape: {X_train_for_lime.shape}")

        print(f"Instance to explain shape: {X_scaled.shape}")



        # Create LIME explainer with the corrected training data

        explainer = LimeTabularExplainer(

            training_data=X_train_for_lime,  # Use the corrected training data

            feature_names=feature_names,

            class_names=[str(cls) for cls in models['label_encoder'].classes_],

            mode='classification',

            discretize_continuous=True,

            sample_around_instance=True,

            random_state=42

        )



        # Create a wrapper function for predict_proba that handles input properly

        def predict_proba_wrapper(X_input):

            """Wrapper to handle input format for model prediction"""

            # Ensure X_input is 2D

            if len(X_input.shape) == 1:

                X_input = X_input.reshape(1, -1)

            elif len(X_input.shape) == 2 and X_input.shape[0] == 1:

                pass  # Already correct shape

            elif len(X_input.shape) == 2:

                # Multiple samples - this is expected for LIME

                pass

            

            # Ensure it's dense

            if hasattr(X_input, 'toarray'):

                X_input = X_input.toarray()

                

            print(f"Predict wrapper input shape: {X_input.shape}")

            return models['crop_model'].predict_proba(X_input)



        # Get the instance to explain - ensure it's 1D for LIME

        instance_to_explain = X_scaled[0].flatten()  # Ensure 1D

        print(f"Instance to explain final shape: {instance_to_explain.shape}")



        # Explain the instance with error handling

        try:

            explanation = explainer.explain_instance(

                instance_to_explain,

                predict_proba_wrapper,

                num_features=min(15, X_scaled.shape[1]),

                num_samples=500  # Reduce for faster computation

            )

        except Exception as lime_error:

            print(f"LIME explanation error: {lime_error}")

            # Try with even fewer samples

            explanation = explainer.explain_instance(

                instance_to_explain,

                predict_proba_wrapper,

                num_features=min(10, X_scaled.shape[1]),

                num_samples=100

            )



        # Get explanation with better error handling

        pred_idx = None

        try:

            # Find the index of predicted class

            pred_idx = int(np.where(models['label_encoder'].classes_ == predicted_class)[0][0])

        except IndexError:

            print(f"Warning: Predicted class '{predicted_class}' not found in label encoder classes")

            pred_idx = 0



        # Get available labels from explanation

        available_labels = list(explanation.local_exp.keys())

        print(f"Available explanation labels: {available_labels}")

        print(f"Predicted class index: {pred_idx}")



        # Use the first available label if pred_idx is not available

        if pred_idx not in available_labels and available_labels:

            pred_idx = available_labels[0]

            print(f"Using alternative label: {pred_idx}")



        try:

            exp_list = explanation.as_list(label=pred_idx)

        except (KeyError, IndexError) as e:

            print(f"Error getting explanation: {e}")

            if available_labels:

                exp_list = explanation.as_list(label=available_labels[0])

                print(f"Used fallback label: {available_labels[0]}")

            else:

                return json.dumps({"error": "No explanations available from LIME"})



        # Check if exp_list is empty

        if not exp_list:

            return json.dumps({"error": "LIME returned empty explanation list"})



        # Process explanations with safety checks

        exp_df = pd.DataFrame(exp_list, columns=['Feature', 'Impact'])

        

        if exp_df.empty:

            return json.dumps({"error": "No feature explanations generated"})

            

        exp_df['Abs_Impact'] = exp_df['Impact'].abs()

        exp_df = exp_df.sort_values('Abs_Impact', ascending=False)



        def get_feature_display_name(feature_str):

            """Convert technical feature names to user-friendly display names"""

            feature_str = str(feature_str)

            

            # Handle state names

            if "encoder__State_Name_" in feature_str:

                state = feature_str.replace("encoder__State_Name_", "").replace("_", " ").title()

                return f"State: {state}"

            

            # Handle crop types

            if "encoder__Crop_Type_" in feature_str:

                crop_type = feature_str.replace("encoder__Crop_Type_", "").replace("_", " ").title()

                return f"Crop Season: {crop_type}"

            

            # Handle remainder features (numerical)

            if "remainder__" in feature_str:

                feature_mapping = {

                    "remainder__N": "Nitrogen (N)",

                    "remainder__P": "Phosphorus (P)",

                    "remainder__K": "Potassium (K)",

                    "remainder__ph": "pH Level",

                    "remainder__rainfall": "Rainfall (mm)",

                    "remainder__temperature": "Temperature (°C)",

                    "remainder__Area_in_hectares": "Area (hectares)",

                    "remainder__Production_in_tons": "Production (tons)",

                    "remainder__Yield_ton_per_hec": "Yield (tons/ha)",

                    "remainder__Humidity_calculated": "Humidity (%)"

                }

                return feature_mapping.get(feature_str, feature_str.replace("remainder__", ""))

            

            # Fallback for any other features

            return feature_str



        exp_df['Display_Name'] = exp_df['Feature'].apply(get_feature_display_name)



        # Add current values with proper mapping

        exp_df['Current_Value'] = "N/A"

        original_features = features_df.iloc[0].to_dict()

        

        for i, feature in enumerate(exp_df['Feature']):

            feature_str = str(feature)

            

            # Map transformed feature names back to original feature names

            if "remainder__" in feature_str:

                original_feature = feature_str.replace("remainder__", "")

                if original_feature in original_features:

                    try:

                        value = original_features[original_feature]

                        if pd.notna(value):

                            exp_df.loc[i, 'Current_Value'] = round(float(value), 2)

                    except (ValueError, TypeError):

                        exp_df.loc[i, 'Current_Value'] = str(value)[:10]

            

            elif "encoder__State_Name_" in feature_str:

                # For state features, show if this state is selected (1) or not (0)

                state_name = feature_str.replace("encoder__State_Name_", "").replace("_", " ")

                if "State_Name" in original_features:

                    current_state = str(original_features["State_Name"]).lower()

                    exp_df.loc[i, 'Current_Value'] = "Yes" if state_name.lower() == current_state else "No"

                    

            elif "encoder__Crop_Type_" in feature_str:

                # For crop type features, show if this type is selected

                crop_type = feature_str.replace("encoder__Crop_Type_", "").replace("_", " ")

                if "Crop_Type" in original_features:

                    current_crop_type = str(original_features["Crop_Type"]).lower()

                    exp_df.loc[i, 'Current_Value'] = "Yes" if crop_type.lower() == current_crop_type else "No"



        # Determine impact direction

        exp_df['Direction'] = 'Neutral'

        exp_df.loc[exp_df['Impact'] > 0.00, 'Direction'] = 'Positive'

        exp_df.loc[exp_df['Impact'] < 0.00, 'Direction'] = 'Negative'



        def get_advice_for_feature(feature_str, impact_value):

            """Generate specific advice based on feature name and impact"""

            feature_str = str(feature_str)

            

            if impact_value > 0.00:

                # Positive impact advice

                if "remainder__N" in feature_str:

                    return "Current nitrogen level supports good crop growth - maintain this level."

                elif "remainder__P" in feature_str:

                    return "Phosphorus level is beneficial for the crop - continue current fertilization."

                elif "remainder__K" in feature_str:

                    return "Potassium level supports crop health - maintain potassium application."

                elif "remainder__rainfall" in feature_str:

                    return "Current rainfall level is favorable for crop growth."

                elif "remainder__temperature" in feature_str:

                    return "Temperature conditions are suitable for this crop."

                elif "remainder__ph" in feature_str:

                    return "Soil pH is at an optimal level for crop growth."

                elif "remainder__Humidity_calculated" in feature_str:

                    return "Humidity level is beneficial for crop development."

                elif "encoder__State_Name_" in feature_str:

                    return "Current location/climate is well-suited for this crop."

                elif "encoder__Crop_Type_" in feature_str:

                    return "This crop season timing is optimal for your conditions."

                else:

                    return "This factor positively influences crop growth."

            else:

                # Negative impact advice

                if "remainder__N" in feature_str:

                    return "Consider adjusting nitrogen fertilizer - may be too high or too low."

                elif "remainder__P" in feature_str:

                    return "Review phosphorus fertilizer application for better results."

                elif "remainder__K" in feature_str:

                    return "Potassium levels may need adjustment - consider soil testing."

                elif "remainder__rainfall" in feature_str:

                    return "Consider irrigation planning or drainage solutions."

                elif "remainder__temperature" in feature_str:

                    return "Monitor temperature - may need crop protection measures."

                elif "remainder__ph" in feature_str:

                    return "Soil pH adjustment may improve crop performance."

                elif "remainder__Humidity_calculated" in feature_str:

                    return "Monitor humidity levels to prevent diseases."

                elif "encoder__State_Name_" in feature_str:

                    return "Consider climate-adapted varieties for your region."

                elif "encoder__Crop_Type_" in feature_str:

                    return "Consider adjusting planting season for better results."

                else:

                    return "This factor may need attention for optimal results."



        exp_df['Advice'] = exp_df.apply(lambda x: get_advice_for_feature(x['Feature'], x['Impact']), axis=1)



        # Create visualization with ENHANCED BEAUTIFUL TABLE STYLING

        try:

            plt.style.use('seaborn-v0_8')  # Use seaborn style for better aesthetics

            fig = plt.figure(figsize=(24, 18))

            gs = plt.GridSpec(2, 2, height_ratios=[1, 1], width_ratios=[1.8, 1.2], 

                             hspace=0.3, wspace=0.3)



            # ================================

            # BEAUTIFUL ENHANCED TABLE STYLING

            # ================================

            ax1 = plt.subplot(gs[0, 0])

            ax1.axis('tight')

            ax1.axis('off')



            # Limit to top 10 features for better readability

            display_df = exp_df.head(10)

            

            # Create enhanced table data with icons and formatting

            table_data = [['🔍 Feature', '📊 Value', '🎯 Impact', '📈 Score', '🔔 Status']]

            

            # Enhanced color scheme

            colors = [['#2E8B57', '#2E8B57', '#2E8B57', '#2E8B57', '#2E8B57']]  # Dark sea green header

            

            for _, row in display_df.iterrows():

                # Enhanced impact direction with icons

                if row['Direction'] == 'Positive':

                    impact_display = f"↗️ BOOST +{abs(row['Impact']):.3f}"

                    status_display = "✅ GOOD"

                    row_color = ['#E8F5E8', '#E8F5E8', '#C8E6C9', '#C8E6C9', '#A5D6A7']  # Light green gradient

                elif row['Direction'] == 'Negative':

                    impact_display = f"↘️ REDUCE -{abs(row['Impact']):.3f}"

                    status_display = "⚠️ REVIEW"

                    row_color = ['#FFEBEE', '#FFEBEE', '#FFCDD2', '#FFCDD2', '#EF9A9A']  # Light red gradient

                else:

                    impact_display = f"➡️ NEUTRAL {row['Impact']:.3f}"

                    status_display = "ℹ️ STABLE"

                    row_color = ['#F3F4F6', '#F3F4F6', '#E5E7EB', '#E5E7EB', '#D1D5DB']  # Light gray gradient

                

                # Format value display

                if isinstance(row['Current_Value'], (int, float)) and pd.notna(row['Current_Value']):

                    value_display = f"{row['Current_Value']:.2f}"

                else:

                    value_display = str(row['Current_Value'])

                

                # Truncate feature name for better display

                feature_name = row['Display_Name'][:28] + "..." if len(row['Display_Name']) > 28 else row['Display_Name']

                

                table_data.append([

                    feature_name,

                    value_display,

                    impact_display,

                    f"★ {abs(row['Impact']):.3f}",

                    status_display

                ])

                colors.append(row_color)



            # Create the beautiful table

            table = ax1.table(cellText=table_data, cellLoc='center', loc='center', 

                             colWidths=[0.35, 0.15, 0.2, 0.15, 0.15], 

                             cellColours=colors)

            

            # Enhanced table styling

            table.auto_set_font_size(False)

            table.set_fontsize(11)

            table.scale(1, 2.2)  # Make table taller

            

            # Style header row

            for i in range(5):

                cell = table[(0, i)]

                cell.set_text_props(weight='bold', color='white', fontsize=12)

                cell.set_facecolor('#2E8B57')

                cell.set_edgecolor('white')

                cell.set_linewidth(2)

            

            # Style data rows with enhanced borders and effects

            for i in range(1, len(table_data)):

                for j in range(5):

                    cell = table[(i, j)]

                    cell.set_text_props(fontsize=10, weight='bold' if j in [2, 4] else 'normal')

                    cell.set_edgecolor('#FFFFFF')

                    cell.set_linewidth(1.5)

                    

                    # Add special formatting for impact and status columns

                    if j == 2:  # Impact column

                        cell.set_text_props(weight='bold', fontsize=11)

                    elif j == 4:  # Status column

                        cell.set_text_props(weight='bold', fontsize=10)



            # Enhanced title with styling

            title_text = f'🌾 LIME Feature Impact Analysis - {predicted_class.upper()}'

            ax1.set_title(title_text, fontsize=18, fontweight='bold', 

                         color='#2E8B57', pad=25,

                         bbox=dict(boxstyle="round,pad=0.5", facecolor='#F0F8F0', 

                                  edgecolor='#2E8B57', linewidth=2))



            # ================================

            # ENHANCED BAR CHART

            # ================================

            ax2 = plt.subplot(gs[0, 1])

            top_features = exp_df.head(8)  # Show more features

            

            if not top_features.empty:

                feature_names_display = [name[:25] + "..." if len(name) > 25 else name 

                                       for name in top_features['Display_Name']]

                impact_values = top_features['Impact'].tolist()

                

                # Enhanced color scheme for bars

                bar_colors = []

                for imp in impact_values:

                    if imp > 0.00:

                        bar_colors.append('#4CAF50')  # Green for positive

                    elif imp < 0.00:

                        bar_colors.append('#F44336')  # Red for negative

                    else:

                        bar_colors.append('#9E9E9E')  # Gray for neutral



                y_pos = np.arange(len(feature_names_display))

                bars = ax2.barh(y_pos, impact_values, color=bar_colors, alpha=0.8, 

                               edgecolor='white', linewidth=1.5)

                

                # Enhanced styling

                ax2.set_yticks(y_pos)

                ax2.set_yticklabels(feature_names_display, fontsize=10, fontweight='bold')

                ax2.invert_yaxis()

                ax2.set_xlabel('Impact Score', fontsize=12, fontweight='bold')

                ax2.set_title('📊 Feature Impact Distribution', fontsize=14, fontweight='bold', 

                             color='#2E8B57', pad=15)

                

                # Enhanced grid

                ax2.grid(axis='x', linestyle='--', alpha=0.4, color='#2E8B57')

                ax2.axvline(x=0, color='#2E8B57', linestyle='-', alpha=0.6, linewidth=2)

                

                # Style the axes

                ax2.spines['top'].set_visible(False)

                ax2.spines['right'].set_visible(False)

                ax2.spines['bottom'].set_color('#2E8B57')

                ax2.spines['left'].set_color('#2E8B57')

                

                # Add value labels on bars with enhanced styling

                for i, (bar, val) in enumerate(zip(bars, impact_values)):

                    label_color = 'white' if abs(val) > 0.00 else 'black'

                    ax2.text(val/2 if abs(val) > 0.00 else val + (0.00 if val > 0 else 0.00), 

                            i, f'{val:.3f}', 

                            va='center', ha='center' if abs(val) > 0.00 else ('left' if val > 0 else 'right'), 

                            fontsize=9, fontweight='bold', color=label_color)



            # ================================

            # ENHANCED ADVICE SECTION

            # ================================

            ax3 = plt.subplot(gs[1, :])

            ax3.axis('off')



            top_advice = exp_df.head(4)

            advice_title = f"🎯 Smart Farming Recommendations for {predicted_class.title()}"

            

            # Create beautiful advice text with enhanced formatting

            advice_text = ""

            icons = ["🌱", "💧", "🌡️", "⚡"]

            

            for i, (_, row) in enumerate(top_advice.iterrows()):

                icon = icons[i] if i < len(icons) else "🔸"

                advice_text += f"{icon} {row['Advice']}\n\n"

            

            # Add general recommendations with icons

            advice_text += "🔍 Monitor field conditions regularly for optimal results\n"

            advice_text += "🔄 Consider crop rotation to maintain soil health\n"

            advice_text += "👨‍🌾 Consult local agricultural experts for region-specific advice\n"

            advice_text += "📱 Use precision agriculture tools for better monitoring"



            # Enhanced advice box styling

            props = dict(boxstyle='round,pad=1.5', facecolor='#F0F8F0', alpha=0.9, 

                        edgecolor='#2E8B57', linewidth=3)

            ax3.text(0.5, 0.5, advice_text, transform=ax3.transAxes, fontsize=13, 

                    verticalalignment='center', horizontalalignment='center', 

                    bbox=props, linespacing=1.5)

            

            # Enhanced advice title

            ax3.set_title(advice_title, fontsize=18, fontweight='bold', color='#2E8B57', 

                         pad=20, bbox=dict(boxstyle="round,pad=0.8", facecolor='#E8F5E8', 

                                          edgecolor='#2E8B57', linewidth=2))



            # Add a subtle background color to the entire figure

            fig.patch.set_facecolor('#FAFAFA')

            

            # Save plot with enhanced settings

            buf = BytesIO()

            plt.tight_layout()

            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 

                       facecolor='#FAFAFA', edgecolor='none')

            buf.seek(0)

            img_str = base64.b64encode(buf.read()).decode('utf-8')

            plt.close()

            

        except Exception as plot_error:

            print(f"Visualization error: {plot_error}")

            img_str = ""



        # Prepare response with safety checks

        features_importance = []

        for _, row in exp_df.head(12).iterrows():

            features_importance.append({

                'Display_Name': row['Display_Name'],

                'Impact': float(row['Impact']),

                'Direction': row['Direction'],

                'Advice': row['Advice'],

                'Current_Value': row['Current_Value']

            })



        top_advice_list = [row['Advice'] for _, row in exp_df.head(5).iterrows()]



        result = {

            "status": "success",

            "predicted_crop": predicted_class,

            "feature_importance": features_importance,

            "top_advice": top_advice_list,

            "visualization": {

                "image_base64": img_str,

                "format": "png"

            } if img_str else {},

            "summary": {

                "total_features_analyzed": len(exp_df),

                "positive_impact_features": len(exp_df[exp_df['Direction'] == 'Positive']),

                "negative_impact_features": len(exp_df[exp_df['Direction'] == 'Negative']),

                "neutral_impact_features": len(exp_df[exp_df['Direction'] == 'Neutral']),

                "model_confidence": "High" if len(exp_df) > 5 else "Medium"

            }

        }



        return json.dumps(result, indent=2)



    except Exception as e:

        import traceback

        error_result = {

            "status": "error",

            "error_message": str(e),

            "error_type": type(e).__name__,

            "traceback": traceback.format_exc(),

            "debug_info": {

                "X_train_shape": getattr(X_train, 'shape', 'Not available') if 'X_train' in locals() else 'Not available',

                "X_scaled_shape": getattr(X_scaled, 'shape', 'Not available') if 'X_scaled' in locals() else 'Not created',

                "predicted_class": locals().get('predicted_class', 'Not predicted')

            }

        }

        return json.dumps(error_result, indent=2)
# Example usage function for API endpoint
def process_lime_explanation_request(request_data: Dict[str, Any]) -> str:

    """
    Process a LIME explanation request for API endpoint
    
    Parameters:
    -----------
    request_data: Dictionary containing:
        - input_features: Dict with feature values
        - models: Loaded model objects
        - X_train: Training data
        - feature_names: List of feature names
    
    Returns:
    --------
    JSON string response
    """
    try:
        input_features = request_data.get('input_features', {})
        models = request_data.get('models', {})
        X_train = request_data.get('X_train')
        feature_names = request_data.get('feature_names', [])
        
        # Validate required parameters
        if not input_features:
            return json.dumps({"status": "error", "error_message": "input_features is required"})
        
        if not models:
            return json.dumps({"status": "error", "error_message": "models is required"})
        
        if X_train is None:
            return json.dumps({"status": "error", "error_message": "X_train is required"})
        
        if not feature_names:
            return json.dumps({"status": "error", "error_message": "feature_names is required"})
        
        # Call the main function
        return explain_with_lime_api(input_features, models, X_train, feature_names)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error_message": f"Request processing failed: {str(e)}",
            "error_type": type(e).__name__
        }
        return json.dumps(error_result, indent=2)
    


