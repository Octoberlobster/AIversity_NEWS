// utils.js
export function getOrCreateUserId() {
  let userId = localStorage.getItem("user_id");
  if (!userId) {
    userId = crypto.randomUUID(); // 生成唯一 ID
    localStorage.setItem("user_id", userId);
  }
  return userId;
}
export function createRoomId() {
  return crypto.randomUUID();
}