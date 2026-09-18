from backend.models.state import PersonalWishesState

def generate_document(state: PersonalWishesState) -> str:
    lines = []
    
    lines.append("# PERSONAL WISHES DOCUMENT")
    lines.append("")
    lines.append("**FICTIONAL DOCUMENT - NOT LEGAL ADVICE**")
    lines.append("")
    
    lines.append("## Personal Information")
    name = state.full_name if state.full_name is not None else "Not provided"
    lines.append(f"- **Full Name:** {name}")
    
    address = state.home_address if state.home_address is not None else "Not provided"
    lines.append(f"- **Home Address:** {address}")
    
    lines.append("")
    lines.append("## Asset Details")
    if state.covers_worldwide_assets is True:
        assets_text = "Yes, covers worldwide assets"
    elif state.covers_worldwide_assets is False:
        assets_text = "No, does not cover worldwide assets"
    else:
        assets_text = "Not provided"
    lines.append(f"- **Covers Worldwide Assets:** {assets_text}")
    
    lines.append("")
    lines.append("## Family")
    if state.has_children is True:
        children_text = "Yes"
        if state.children_names:
            children_names_text = ", ".join(state.children_names)
        else:
            children_names_text = "Names not provided"
    elif state.has_children is False:
        children_text = "No"
        children_names_text = "N/A"
    else:
        children_text = "Not provided"
        children_names_text = "Not provided"
        
    lines.append(f"- **Has Children:** {children_text}")
    if state.has_children is True:
        lines.append(f"- **Children's Names:** {children_names_text}")
        
    lines.append("")
    lines.append("## Executor Appointment")
    exec_name = state.executor.name if state.executor.name is not None else "Not provided"
    exec_rel = state.executor.relationship if state.executor.relationship is not None else "Not provided"
    lines.append(f"- **Executor Name:** {exec_name}")
    lines.append(f"- **Relationship:** {exec_rel}")
    
    lines.append("")
    lines.append("## Specific Gifts")
    if state.specific_gifts is None:
        gifts_text = "Not provided"
    elif len(state.specific_gifts) == 0:
        gifts_text = "No specific gifts"
    else:
        gifts_text = "\n" + "\n".join(f"  - {g}" for g in state.specific_gifts)
    lines.append(f"**Gifts:** {gifts_text}")
    
    lines.append("")
    lines.append("## Additional Wishes")
    if state.additional_wishes is None:
        wishes_text = "Not provided"
    elif state.additional_wishes.strip() == "":
        wishes_text = "None"
    else:
        wishes_text = state.additional_wishes
    lines.append(f"{wishes_text}")
    
    return "\n".join(lines)
