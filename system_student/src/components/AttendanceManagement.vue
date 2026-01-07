<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const students = ref([])
const attendances = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const currentAttendance = ref({
  student_id: '',
  course_id: '',
  date: '',
  status: '',
  reason: ''
})
const errorMessage = ref('')
const selectedCourse = ref('')
const courses = ref([])
const studentCourses = ref([])  // 存储学生选课记录

const page = ref(1)
const limit = 10
const total = ref(0)

const filteredAttendances = computed(() => {
  if (!searchKeyword.value.trim()) {
    return attendances.value
  }
  const keyword = searchKeyword.value.toLowerCase().trim()
  return attendances.value.filter(att => {
    return (
      (att.student_name && att.student_name.toLowerCase().includes(keyword)) ||
      (att.student_id && att.student_id.toLowerCase().includes(keyword)) ||
      (att.course_name && att.course_name.toLowerCase().includes(keyword)) ||
      (att.date && att.date.includes(keyword)) ||
      (att.status && att.status.toLowerCase().includes(keyword)) ||
      (att.reason && att.reason.toLowerCase().includes(keyword))
    )
  })
})

const fetchStudents = async () => {
  try {
    // 获取所有学生（不分页，用于下拉选择）
    const response = await axios.get('/api/students', {
      params: { page: 1, limit: 1000 }
    })
    students.value = response.data.data || response.data || []
  } catch (error) {
    console.error('Error fetching students:', error)
    students.value = []
  }
}

const fetchCourses = async () => {
  try {
    // 获取所有课程（不分页，用于下拉选择）
    const response = await axios.get('/api/courses', {
      params: { page: 1, limit: 1000 }
    })
    courses.value = response.data.data || response.data || []
  } catch (error) {
    console.error('Error fetching courses:', error)
    courses.value = []
  }
}

const fetchStudentCourses = async () => {
  try {
    const response = await axios.get('/api/student-courses')
    studentCourses.value = response.data || []
  } catch (error) {
    console.error('Error fetching student courses:', error)
    studentCourses.value = []
  }
}

// 获取指定学生已选的课程列表
const getStudentCourses = computed(() => {
  if (!currentAttendance.value.student_id) {
    return []  // 如果没有选择学生，返回空列表
  }
  
  // 从studentCourses中筛选出该学生已选的课程
  const selectedCourses = studentCourses.value.filter(sc => {
    return sc.student_id === currentAttendance.value.student_id
  })
  
  // 从courses中获取这些课程的详细信息
  const courseDetails = selectedCourses.map(sc => {
    const course = courses.value.find(c => c.id === sc.course_id)
    return course ? { ...course, student_course_id: sc.id } : null
  }).filter(c => c !== null)
  
  // 如果是编辑模式，并且当前记录的课程不在已选课程中，也要包含它（保持原有值）
  if (isEdit.value && currentAttendance.value.course_id) {
    const currentCourseId = parseInt(currentAttendance.value.course_id)
    const alreadyIncluded = courseDetails.some(c => c.id === currentCourseId)
    if (!alreadyIncluded) {
      const currentCourse = courses.value.find(c => c.id === currentCourseId)
      if (currentCourse) {
        courseDetails.push({ ...currentCourse })
      }
    }
  }
  
  return courseDetails
})

const fetchAttendances = async () => {
  try {
    const params = {
      course_id: selectedCourse.value,
      page: page.value,
      limit
    }
    const response = await axios.get('/api/attendance', { params })
    attendances.value = response.data.data
    total.value = response.data.total
  } catch (error) {
    console.error('Error fetching attendances:', error)
  }
}

const resetForm = () => {
  currentAttendance.value = {
    student_id: '',
    course_id: '',
    date: '',
    status: '',
    reason: ''
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  console.log('Submitting attendance data:', currentAttendance.value)  // Debug log
  
  // 准备提交数据，确保数据类型正确
  const submitData = {
    student_id: currentAttendance.value.student_id || null,
    course_id: currentAttendance.value.course_id || null,
    date: currentAttendance.value.date || null,
    status: currentAttendance.value.status || '',
    reason: currentAttendance.value.reason || ''
  }
  
  // 处理course_id：如果是空字符串或0，转为null
  if (submitData.course_id === '' || submitData.course_id === 0 || submitData.course_id === '0') {
    submitData.course_id = null
  } else if (submitData.course_id) {
    // 确保course_id是整数
    const courseIdNum = parseInt(submitData.course_id)
    submitData.course_id = isNaN(courseIdNum) ? null : courseIdNum
  }
  
  try {
    if (isEdit.value) {
      const response = await axios.put(`/api/attendance/${currentAttendance.value.id}`, submitData)
      if (response.data.success) {
        alert('考勤记录更新成功')
      }
    } else {
      const response = await axios.post('/api/attendance', submitData)
      if (response.data.success) {
        alert('考勤记录添加成功')
      }
    }
    showForm.value = false
    resetForm()
    await fetchAttendances()
  } catch (error) {
    console.error('Submit error:', error)  // Debug log
    console.error('Error response:', error.response)  // Debug log
    errorMessage.value = error.response?.data?.message || '操作失败'
    alert(errorMessage.value)
  }
}

const handleStudentChange = () => {
  // 当学生改变时，清空课程选择（因为课程列表会改变）
  // 只有在新增模式下才清空，编辑模式下保持原有课程
  if (!isEdit.value) {
    currentAttendance.value.course_id = ''
  } else {
    // 编辑模式下，如果当前课程不在该学生已选课程中，清空课程选择
    const validCourses = getStudentCourses.value
    if (currentAttendance.value.course_id) {
      const courseId = parseInt(currentAttendance.value.course_id)
      const isValid = validCourses.some(c => c.id === courseId)
      if (!isValid) {
        currentAttendance.value.course_id = ''
      }
    }
  }
}

const editAttendance = (att) => {
  currentAttendance.value = { ...att }
  // 确保course_id是正确的类型（可能是字符串需要转为数字）
  if (currentAttendance.value.course_id) {
    currentAttendance.value.course_id = parseInt(currentAttendance.value.course_id) || null
  }
  isEdit.value = true
  showForm.value = true
}

const deleteAttendance = async (id) => {
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/attendance/${id}`)
      await fetchAttendances()
    } catch (error) {
      console.error('Error deleting attendance:', error)
    }
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchAttendances()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

onMounted(() => {
  fetchStudents()
  fetchCourses()
  fetchStudentCourses()  // 获取学生选课记录
  fetchAttendances()
})
</script>

<template>
  <div>
    <div class="toolbar">
      <select v-model="selectedCourse" @change="() => { page = 1; fetchAttendances() }" class="course-select">
        <option value="">所有课程</option>
        <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.course_name }}</option>
      </select>
      <button @click="showForm = true; resetForm()" class="add-button-green">
        <span style="margin-right: 6px;">➕</span>添加考勤
      </button>
      <div class="search-container">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="🔍 搜索考勤（学生姓名、学号、课程、日期、状态、原因）" 
          class="search-input"
        />
        <span v-if="searchKeyword" class="search-result">
          找到 {{ filteredAttendances.length }} 条记录
        </span>
      </div>
    </div>
    
    <table v-if="filteredAttendances.length">
      <thead>
        <tr>
          <th>学生姓名</th>
          <th>课程</th>
          <th>日期</th>
          <th>状态</th>
          <th>原因</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="att in filteredAttendances" :key="att.id">
          <td>{{ att.student_name }}</td>
          <td>{{ att.course_name || '无' }}</td>
          <td>{{ att.date }}</td>
          <td>{{ att.status }}</td>
          <td>{{ att.reason }}</td>
          <td>
            <button @click="editAttendance(att)">编辑</button>
            <button @click="deleteAttendance(att.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!searchKeyword">暂无考勤记录</p>
    <p v-else>未找到匹配的考勤记录</p>

    <div v-if="total > 0" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <div v-if="showForm" class="modal">
      <div class="modal-content">
        <h2>{{ isEdit ? '编辑考勤' : '添加考勤' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group">
            <select v-model="currentAttendance.student_id" required @change="handleStudentChange">
              <option value="">选择学生</option>
              <option v-for="student in students" :key="student.student_id" :value="student.student_id">{{ student.name }}</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学生: 选择一位学生</div>
            </div>
          </div>
          <div class="form-group">
            <select v-model="currentAttendance.course_id" :disabled="!currentAttendance.student_id">
              <option value="">选择课程 (可选)</option>
              <option v-if="!currentAttendance.student_id" value="" disabled>请先选择学生</option>
              <option v-else-if="getStudentCourses.length === 0" value="" disabled>该学生未选任何课程</option>
              <option v-for="course in getStudentCourses" :key="course.id" :value="course.id">
                {{ course.course_name }}
              </option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">
                课程: {{ !currentAttendance.student_id ? '请先选择学生' : '只能选择该学生已选的课程' }}
              </div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentAttendance.date" type="date" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">日期: 考勤日期</div>
            </div>
          </div>
          <div class="form-group">
            <select v-model="currentAttendance.status" required>
              <option value="">选择状态</option>
              <option value="出勤">出勤</option>
              <option value="缺席">缺席</option>
              <option value="请假">请假</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">状态: 出勤/缺席/请假</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentAttendance.reason" placeholder="原因（可选）" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">原因: 可选，说明原因</div>
            </div>
          </div>
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <div class="buttons">
            <button type="submit">保存</button>
            <button type="button" @click="showForm = false">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 绿色主题 - 考勤管理 */
/* 主表格样式 */
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

th {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: none;
  position: sticky;
  top: 0;
  z-index: 10;
}

td {
  padding: 14px 12px;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

tbody tr {
  transition: all 0.2s ease;
}

tbody tr:hover {
  background-color: #f1f8e9;
  transform: scale(1.001);
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.1);
}

tbody tr:last-child td {
  border-bottom: none;
}

/* 按钮样式 */
button {
  margin: 0 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

td button:first-of-type {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
}

td button:last-of-type {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
  color: white;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
}

.course-select {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.course-select:focus {
  outline: none;
  border-color: #4caf50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.add-button-green {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  white-space: nowrap;
}

.add-button-green:hover {
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}

.search-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
}

.search-input {
  flex: 1;
  max-width: 500px;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #4caf50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.search-result {
  color: #4caf50;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

/* 模态框 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border: none;
  padding: 30px;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-content h2 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 24px;
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

form {
  display: flex;
  flex-direction: column;
}

.form-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  position: relative;
}

input, select {
  flex: 1;
  background: #f8f9fa;
  border: 2px solid #e0e0e0;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

input:focus, select:focus {
  outline: none;
  border-color: #4caf50;
  background: white;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.info-container {
  position: relative;
  margin-left: 10px;
}

.info-ellipsis {
  cursor: pointer;
  color: #4caf50;
  font-weight: bold;
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e8f5e9;
  transition: all 0.3s ease;
}

.info-ellipsis:hover {
  background: #4caf50;
  color: white;
  transform: scale(1.1);
}

.tooltip {
  display: none;
  position: absolute;
  background: #333;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  white-space: nowrap;
  top: -40px;
  left: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  font-size: 12px;
  z-index: 100;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 20px;
  border: 6px solid transparent;
  border-top-color: #333;
}

.info-container:hover .tooltip {
  display: block;
}

button[type="submit"], button[type="button"] {
  width: 120px;
  height: 44px;
  border-radius: 8px;
  cursor: pointer;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

button[type="submit"] {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
}

button[type="submit"]:hover {
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}

button[type="button"] {
  background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
}

.error {
  color: #f44336;
  background: #ffebee;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 15px;
  border-left: 4px solid #f44336;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.pagination button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #4caf50;
  font-weight: 500;
}

p[style*="color: #999"] {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
</style>

