from IPython.core.display import display
from IPython.core.display import HTML
import ipywidgets as ui

# Display input element with ID
display(ui.HTML("<input type=file id=c-file-uploader>"))

# Display Javascript code to:
#   1. get the file that user had selected to upload
#   2. encode the file in Base64 string
#   3. break the file into chunks
#   4. upload the file in chunks (using Jupyter's upload API)
display(
    HTML(
        """
        <script>             
            document.getElementById("c-file-uploader").onchange = function () {
                // Get file
                var file = this.files[0]

                // Encode file in Base64 (by converting it into a DataURL)
                let reader = new FileReader()
                reader.readAsDataURL(file);

                // Proceed to upload file if encoding was successful 
                reader.onload = function () {
                    var encodedFile = reader.result
                        .replace("data:", "")       // Replace unnecessary characters in DataURL
                        .replace(/^.+,/, "")        // https://pqina.nl/blog/convert-a-file-to-a-base64-string-with-javascript/

                    // Break file into chunks 
                    let startIndex = 0
                    let endIndex = file.size
                    let chunkSize = 1024 * 1024     // 1MB
                    let chunks = []

                    while(startIndex < endIndex) {
                        let newStartIndex = startIndex + chunkSize
                        chunks.push(encodedFile.slice(startIndex, newStartIndex))
                        startIndex = newStartIndex
                    }
                    console.log({chunks})

                    // Upload file in chunks 
                    for (let i = 0; i < chunks.length; i++) {
                    
                        // Jupyter's upload API requires chunk number to start with 1 and end with -1
                        let chunk_number = i + 1
                        if (i == chunks.length - 1) chunk_number = -1

                        // Format: <BASE_URL>/notebooks/<PATH_TO_CURRENT_NOTEBOOK>
                        var CURRENT_NOTEBOOK_URL = window.location.href           
                        var BASE_URL = CURRENT_NOTEBOOK_URL.split("/notebooks/")[0]

                        let fileDestinationPath = file.name
                        let url = BASE_URL + "/api/contents/" + fileDestinationPath
                        console.log({url})
                        let data = {
                            content: chunks[i],
                            name: file.name,
                            path: fileDestinationPath,
                            format: "base64",
                            type: "file",
                        }
                        if (chunks.length > 1) data.chunk = chunk_number

                        console.log({i}, {data})

                        var http = new XMLHttpRequest()
                        http.open("PUT", url, true)
                        http.send(JSON.stringify(data))
                    }
                }

                // Display error message if encoding fails
                reader.onerror = function () {
                    alert("Fail to encode file in Base64") 
                }
            }
        </script>
    """
    )
)
