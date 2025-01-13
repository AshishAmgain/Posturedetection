import axios from "axios";

export const uploadVideo = (video) => {
  const formData = new FormData();
  formData.append("video", video);
  return axios.post("http://localhost:5000/upload", formData);
};

export const getFeedback = (feedbackPath) => {
  return axios.get(`http://localhost:5000${feedbackPath}`);
};
