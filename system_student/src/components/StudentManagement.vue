<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  readonly: {
    type: Boolean,
    default: false
  },
  studentId: {
    type: String,
    default: null
  }
})

const students = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const expandedRows = ref([])  // Track expanded rows
const studentCourses = ref({})  // Store courses for each student
const studentAttendances = ref({})  // Store attendances for each student
const showTooltip = ref({})  // Track tooltip visibility
const currentStudent = ref({
  student_id: '',
  name: '',
  gender: '',
  age: '',
  phone: '',
  email: '',
  address: '',
  class_name: '',
  teacher_name: ''
})
const errorMessage = ref('')
const page = ref(1)
const limit = 10
const total = ref(0)

const filteredStudents = computed(() => {
  let filtered = students.value
  
  // 如果是只读模式，确保只显示当前学生的信息
  if (props.readonly && props.studentId) {
    filtered = filtered.filter(s => s.student_id === props.studentId)
  }
  
  if (!searchKeyword.value.trim()) {
    return filtered
  }
  
  const keyword = searchKeyword.value.toLowerCase().trim()
  return filtered.filter(student => {
    return (
      (student.student_id && student.student_id.toLowerCase().includes(keyword)) ||
      (student.name && student.name.toLowerCase().includes(keyword)) ||
      (student.phone && student.phone.toLowerCase().includes(keyword)) ||
      (student.class_name && student.class_name.toLowerCase().includes(keyword)) ||
      (student.teacher_name && student.teacher_name.toLowerCase().includes(keyword))
    )
  })
})

const fetchStudents = async () => {
  try {
    if (props.readonly && props.studentId) {
      // 学生角色：只获取自己的信息，直接通过API查询特定学生
      const response = await axios.get('/api/students', {
        params: { page: 1, limit: 1000 }
      })
      const allData = response.data.data || response.data || []
      // 严格过滤，只保留当前学生的信息
      const myInfo = allData.filter(s => s.student_id === props.studentId)
      students.value = myInfo
      total.value = myInfo.length
      console.log('Student view: Loading only my info. studentId:', props.studentId, 'Found:', myInfo.length)
    } else {
      // 管理员角色：获取所有学生（分页）
      const response = await axios.get('/api/students', {
        params: { page: page.value, limit }
      })
      students.value = response.data.data || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    console.error('Error fetching students:', error)
    students.value = []
    total.value = 0
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchStudents()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

const resetForm = () => {
  currentStudent.value = {
    student_id: '',
    name: '',
    gender: '',
    age: '',
    phone: '',
    email: '',
    address: '',
    class_name: '',
    teacher_name: ''
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  try {
    // 如果是只读模式且是编辑模式，检查是否在编辑自己的信息
    if (props.readonly && isEdit.value) {
      if (currentStudent.value.student_id !== props.studentId) {
        alert('您只能编辑自己的信息')
        return
      }
    }
    
    // 如果是只读模式且是添加模式，不允许添加
    if (props.readonly && !isEdit.value) {
      alert('学生无权添加学生信息')
      return
    }
    
    if (isEdit.value) {
      await axios.put(`/api/students/${currentStudent.value.student_id}`, currentStudent.value)
    } else {
      await axios.post('/api/students', currentStudent.value)
    }
    showForm.value = false
    resetForm()
    await fetchStudents()
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '操作失败'
  }
}

const editStudent = (student) => {
  // 只读模式下只允许编辑自己的信息
  if (props.readonly) {
    if (student.student_id !== props.studentId) {
      alert('您只能编辑自己的信息')
      return
    }
    // 允许编辑自己的信息
  }
  currentStudent.value = { ...student }
  isEdit.value = true
  showForm.value = true
}

const deleteStudent = async (student_id) => {
  // 只读模式下不允许删除（即使是自己的信息也不能删除）
  if (props.readonly) {
    alert('学生无权删除信息')
    return
  }
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/students/${student_id}`)
      // 如果删除后当前页没有数据，返回上一页
      if (students.value.length === 1 && page.value > 1) {
        page.value--
      }
      await fetchStudents()
    } catch (error) {
      console.error('Error deleting student:', error)
    }
  }
}

const toggleExpand = async (studentId) => {
  const index = expandedRows.value.indexOf(studentId)
  if (index === -1) {
    expandedRows.value.push(studentId)
    if (!studentCourses.value[studentId]) {
      await fetchStudentCourses(studentId)
    }
    if (!studentAttendances.value[studentId]) {
      await fetchStudentAttendances(studentId)
    }
  } else {
    expandedRows.value.splice(index, 1)
  }
}

const fetchStudentCourses = async (studentId) => {
  try {
    const response = await axios.get('/api/student-courses', {
      params: { student_id: studentId }
    })
    studentCourses.value[studentId] = response.data || []
    console.log('Fetched courses for student', studentId, ':', studentCourses.value[studentId])
  } catch (error) {
    console.error('Error fetching student courses:', error)
    studentCourses.value[studentId] = []
  }
}

const fetchStudentAttendances = async (studentId) => {
  try {
    const response = await axios.get('/api/attendance', {
      params: { student_id: studentId, limit: 1000 }
    })
    // Handle both paginated and non-paginated responses
    const data = response.data.data || response.data || []
    studentAttendances.value[studentId] = Array.isArray(data) ? data : []
    console.log('Fetched attendances for student', studentId, ':', studentAttendances.value[studentId])
  } catch (error) {
    console.error('Error fetching student attendances:', error)
    studentAttendances.value[studentId] = []
  }
}

const showButtonTooltip = (studentId) => {
  if (!expandedRows.value.includes(studentId)) {
    showTooltip.value[studentId] = true
  }
}

const hideButtonTooltip = (studentId) => {
  showTooltip.value[studentId] = false
}

onMounted(() => {
  fetchStudents()
})
</script>

<template>
  <div>
    <div v-if="!readonly" class="toolbar">
      <button @click="showForm = true; resetForm()" class="add-button">
        <span style="margin-right: 6px;">➕</span>添加学生
      </button>
      <div class="search-container">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="🔍 搜索学生（学号、姓名、电话、班级、班主任）" 
          class="search-input"
        />
        <span v-if="searchKeyword" class="search-result">
          找到 {{ filteredStudents.length }} 条记录
        </span>
      </div>
    </div>
    <div v-else class="student-info-header">
      <h3 class="info-title">我的信息</h3>
      <p v-if="!props.studentId" class="info-hint">提示：未找到对应的学生信息，请联系管理员</p>
      <p v-else class="info-description">您可以查看和编辑自己的信息，但无法删除</p>
    </div>
    
    <table v-if="filteredStudents.length">
      <thead>
        <tr>
          <th></th>  <!-- Expand column -->
          <th>学号</th>
          <th>姓名</th>
          <th>性别</th>
          <th>年龄</th>
          <th>电话</th>
          <th>邮箱</th>
          <th>地址</th>
          <th>班级</th>
          <th>班主任</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="student in filteredStudents" :key="student.student_id || student.id">
          <tr>
            <td>
              <div 
                class="expand-button-container"
                @mouseenter="showButtonTooltip(student.student_id)"
                @mouseleave="hideButtonTooltip(student.student_id)"
              >
                <button 
                  @click.stop="toggleExpand(student.student_id)"
                  class="expand-button"
                >{{ expandedRows.includes(student.student_id) ? '-' : '+' }}</button>
                <div v-if="!expandedRows.includes(student.student_id) && showTooltip[student.student_id]" class="custom-tooltip">
                  该学生所选课程、成绩、出勤
                </div>
              </div>
            </td>
            <td>{{ student.student_id }}</td>
            <td>{{ student.name }}</td>
            <td>{{ student.gender }}</td>
            <td>{{ student.age }}</td>
            <td>{{ student.phone }}</td>
            <td>{{ student.email }}</td>
            <td>{{ student.address }}</td>
            <td>{{ student.class_name }}</td>
            <td>{{ student.teacher_name }}</td>
            <td v-if="!readonly">
              <button @click.stop="editStudent(student)">编辑</button>
              <button @click.stop="deleteStudent(student.student_id)">删除</button>
            </td>
            <td v-else>
              <button @click.stop="editStudent(student)" class="edit-btn">编辑</button>
              <span class="no-delete-hint">无法删除</span>
            </td>
          </tr>
          <tr v-if="expandedRows.includes(student.student_id)" class="expanded-row">
            <td colspan="11" class="expanded-cell">
              <div class="expanded-content">
                <!-- 课程和成绩信息 -->
                <div class="expanded-section">
                  <h4 class="section-title">📚 该学生所选课程及成绩</h4>
                  <table class="sub-table">
                    <thead>
                      <tr>
                        <th>课程名称</th>
                        <th>课程代码</th>
                        <th>考试成绩</th>
                        <th>平时成绩</th>
                        <th>总成绩</th>
                        <th>学期</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="sc in (studentCourses[student.student_id] || [])" :key="sc.id || sc.course_id">
                        <td>{{ sc.course_name || '未知' }}</td>
                        <td>{{ sc.course_code || '未知' }}</td>
                        <td>{{ sc.exam_score ?? 0 }}</td>
                        <td>{{ sc.daily_score ?? 0 }}</td>
                        <td>{{ sc.final_score ?? 0 }}</td>
                        <td>{{ sc.semester || '' }}</td>
                      </tr>
                      <tr v-if="!studentCourses[student.student_id] || studentCourses[student.student_id].length === 0">
                        <td colspan="6" class="empty-state">暂无选课记录</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <!-- 考勤信息 -->
                <div class="expanded-section">
                  <h4 class="section-title">📅 该学生考勤信息</h4>
                  <table class="sub-table">
                    <thead>
                      <tr>
                        <th>日期</th>
                        <th>课程</th>
                        <th>状态</th>
                        <th>原因</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="att in (studentAttendances[student.student_id] || [])" :key="att.id">
                        <td>{{ att.date }}</td>
                        <td>{{ att.course_name || '无' }}</td>
                        <td>{{ att.status }}</td>
                        <td>{{ att.reason || '' }}</td>
                      </tr>
                      <tr v-if="!studentAttendances[student.student_id] || studentAttendances[student.student_id].length === 0">
                        <td colspan="4" class="empty-state">暂无考勤记录</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <p v-else-if="readonly && !props.studentId" style="color: #999;">未找到您的学生信息，请联系管理员</p>
    <p v-else-if="readonly">暂无您的学生信息</p>
    <p v-else-if="!searchKeyword">暂无学生信息</p>
    <p v-else>未找到匹配的学生信息</p>

    <div v-if="total > 0 && !searchKeyword && !readonly" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <div v-if="showForm" class="modal">
      <div class="modal-content">
        <h2>{{ isEdit ? '编辑学生' : '添加学生' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group">
            <input v-model="currentStudent.student_id" placeholder="学号" required :disabled="isEdit" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学号: 唯一标识，不能重复</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.name" placeholder="姓名" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">姓名: 学生的全名</div>
            </div>
          </div>
          <div class="form-group">
            <select v-model="currentStudent.gender" required>
              <option value="">选择性别</option>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">性别: 男或女</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.age" type="number" placeholder="年龄" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">年龄</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.phone" placeholder="电话" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">电话: 手机号码</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.email" placeholder="邮箱" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">邮箱: email</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.address" placeholder="地址" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">地址: （选填）家庭地址</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.class_name" placeholder="班级" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">班级: 班级名称</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudent.teacher_name" placeholder="班主任" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">班主任: 老师姓名</div>
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  background-color: #f8f9ff;
  transform: scale(1.001);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

tbody tr:last-child td {
  border-bottom: none;
}

/* 按钮样式优化 */
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

button:active {
  transform: translateY(0);
}

/* 编辑按钮 */
td button:first-of-type {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
}

td button:first-of-type:hover {
  background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%);
}

/* 删除按钮 */
td button:last-of-type {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
  color: white;
}

td button:last-of-type:hover {
  background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%);
}

/* 模态框样式 */
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.info-container {
  position: relative;
  margin-left: 10px;
}

.info-ellipsis {
  cursor: pointer;
  color: #667eea;
  font-weight: bold;
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0f0ff;
  transition: all 0.3s ease;
}

.info-ellipsis:hover {
  background: #667eea;
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
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

button[type="submit"]:hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

button[type="button"] {
  background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
}

button[type="button"]:hover {
  background: linear-gradient(135deg, #757575 0%, #616161 100%);
  box-shadow: 0 4px 12px rgba(117, 117, 117, 0.4);
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

/* 子表格样式 */
.sub-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 15px 0;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.sub-table th {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  padding: 12px;
  font-size: 13px;
}

.sub-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.sub-table tbody tr:hover {
  background-color: #f1f8e9;
}

/* 展开行样式 */
.expanded-row {
  background: #fafafa;
}

.expanded-cell {
  padding: 0 !important;
  border: none !important;
}

.expanded-content {
  padding: 25px;
  background: linear-gradient(to bottom, #fafafa 0%, #ffffff 100%);
  border-radius: 12px;
  margin: 15px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.03);
}

.expanded-section {
  margin-bottom: 25px;
}

.expanded-section:last-child {
  margin-bottom: 0;
}

.section-title {
  color: #667eea;
  font-weight: 600;
  margin: 0 0 15px 0;
  font-size: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 20px;
  font-style: italic;
}

.edit-btn {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
}

.no-delete-hint {
  color: #999;
  margin-left: 12px;
  font-size: 13px;
  font-style: italic;
}

/* 空状态样式 */
p[style*="color: #999"] {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 搜索框和按钮样式优化 */
input[type="text"][placeholder*="搜索"] {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}

input[type="text"][placeholder*="搜索"]:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

button:not([type="submit"]):not([type="button"]):not(.expand-button) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
}

button:not([type="submit"]):not([type="button"]):not(.expand-button):hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  table {
    font-size: 12px;
  }
  
  th, td {
    padding: 10px 8px;
  }
  
  .modal-content {
    width: 95%;
    padding: 20px;
  }
}
/* 工具栏样式 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.add-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  white-space: nowrap;
}

.search-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  flex: 1;
  max-width: 500px;
}

.search-result {
  color: #667eea;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

/* 学生信息头部 */
.student-info-header {
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.info-title {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 22px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.info-hint {
  color: #ff9800;
  font-size: 14px;
  margin: 8px 0 0 0;
  padding: 10px;
  background: #fff3cd;
  border-radius: 6px;
  border-left: 4px solid #ff9800;
}

.info-description {
  color: #666;
  font-size: 13px;
  margin: 8px 0 0 0;
}

/* 展开按钮样式 */
.expand-button-container {
  position: relative;
  display: inline-block;
}

.expand-button {
  cursor: pointer;
  padding: 6px 12px;
  min-width: 32px;
  height: 32px;
  border: 2px solid #667eea;
  background: linear-gradient(135deg, #f0f0ff 0%, #ffffff 100%);
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-weight: 600;
  color: #667eea;
  font-size: 16px;
}

.expand-button:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}
.custom-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 5px;
  padding: 6px 10px;
  background-color: rgba(0, 0, 0, 0.85);
  color: white;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
  z-index: 10000;
  pointer-events: none;
  animation: tooltipFadeIn 0.1s ease-out;
}
.custom-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.85);
}
@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #667eea;
  font-weight: 500;
}
</style>

