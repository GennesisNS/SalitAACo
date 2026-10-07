// Profile page: the profile picture is uploaded as soon as a file is picked.

const avatarFile = document.getElementById("avatarFile");
document.getElementById("avatarPickBtn").onclick = () => avatarFile.click();
avatarFile.onchange = () => {
  if (avatarFile.files[0]) document.getElementById("avatarForm").submit();
};
