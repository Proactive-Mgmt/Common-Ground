document.getElementById('hopeScaleForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    const formData = new FormData(event.target);
    const jsonOutput = {
        fields: [
            {
                name: "HS_Title",
                type: "Divider",
                label: "Common Ground Hope Scale"
            },
            {
                name: "HS_Subtitle",
                type: "Description",
                label: "",
                value: "Our goal is to better understand how we can help you move from crisis to hope. Your input is important to help us achieve that goal."
            },
            {
                name: "HS_SectionTitle",
                type: "Subtitle",
                label: "How hopeful are you that you can do the following when things aren't going well?"
            },
            {
                name: "HS_ComparisonHope",
                type: "ComparisonTable",
                label: "How hopeful are you that you can do the following when things aren't going well?",
                previous_options: [
                    { label: "No Hope", value: formData.get('question1_before') },
                    { label: "Little Hope", value: formData.get('question1_before') },
                    { label: "Some Hope", value: formData.get('question1_before') },
                    { label: "Strong Hope", value: formData.get('question1_before') }
                ],
                current_options: [
                    { label: "No Hope", value: formData.get('question1_after') },
                    { label: "Little Hope", value: formData.get('question1_after') },
                    { label: "Some Hope", value: formData.get('question1_after') },
                    { label: "Strong Hope", value: formData.get('question1_after') }
                ],
                items: [
                    {label: "Try new solutions to my challenges.", value: "HS_TryNewSolutionsToMyChallenges"},
                    {label: "Find resources to help me.", value: "HS_FindResourcesToHelpMe"},
                    {label: "Contact someone if I need support.", value: "HS_ContactSomeoneIfINeedSupport"},
                    {label: "Meet the goals that I set for myself.", value: "HS_MeetTheGoalsThatISetForMyself"},
                    {label: "Have the ability to identify the things in life that are important to me.", value: "HS_HaveTheAbilityToIdentifyTheThingsInLifeThatAreImportanToMe"}
                ],
                metadata: {
                    gridSize: 12,
                    config: {
                        previous_title: "BEFORE Common Ground Helped Me",
                        current_title: "NOW, After Common Ground Helped Me",
                        previous_value: "HS_ComparisonHopeBefore",
                        current_value: "HS_ComparisonHopeAfter"
                    }
                }
            },
            // Add other fields as necessary
        ]
    };

    console.log(JSON.stringify(jsonOutput)); // Log the JSON output to the console
});