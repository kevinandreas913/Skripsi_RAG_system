Python (requests):
```
import requests

url = "https://domainmu.com/proseschat"
payload = {
    "api_key": "APIKEY_CONTOH",
    "message": "Jelaskan isi dokumen?"
}
response = requests.post(url, json=payload)

print(response.json())
```

JavaScript (fetch):
```
async function callAPI() {
  const response = await fetch("https://domainmu.com/proseschat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      api_key: "APIKEY_CONTOH",
      message: "Jelaskan isi dokumen?"
    }),
  });

  const data = await response.json();
  console.log(data);
}

callAPI();
```

PHP (cURL):
```
<?php
$ch = curl_init("https://domainmu.com/proseschat");
$data = json_encode([
    "api_key" => "APIKEY_CONTOH",
    "message" => "Jelaskan isi dokumen?"
]);

curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: application/json"]);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);

$response = curl_exec($ch);
curl_close($ch);

echo $response;
?>
```