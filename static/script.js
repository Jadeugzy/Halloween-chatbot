const form = document.getElementById("inputForm");
const textInput = document.getElementById("textInput");
const chat = document.getElementById("chat");

function appendMessage(text, cls="bot"){
  const div = document.createElement("div");
  div.className = `msg ${cls}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage(text){
  appendMessage(text, "user");
  textInput.value = "";

  try {
    const res = await fetch("/api/message", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({text})
    });
    const replies = await res.json();
    for(const r of replies){
      let cls = "bot";
      if(r.type === "clue") cls = "clue";
      else if(r.type === "alphabet") cls = "alphabet";
      else if(r.type === "success") cls = "success";
      else if(r.type === "error") cls = "error";
      else if(r.type === "system") cls = "bot";
      appendMessage(r.text, cls);
    }
  } catch (err){
    appendMessage("The spirits are silent... (network error)", "error");
    console.error(err);
  }
}

form.addEventListener("submit", (e)=>{
  e.preventDefault();
  const text = textInput.value.trim();
  if(!text) return;
  sendMessage(text);
});

window.addEventListener("load", ()=>{
  appendMessage("Welcome to AUTOPSY OF THE UNCLAIMED CORPSE.", "bot");
  appendMessage("Type your team's name to begin (examples: conjuring, insidious, the shining, the exorcist, the ring, poltergeist, sinister, scream, evil dead, the grudge).", "bot");
});