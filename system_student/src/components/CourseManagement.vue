<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  readonly: {
    type: Boolean,
    default: false
  }
})

const courses = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const currentCourse = ref({
  course_code: '',
  course_name: '',
  teacher: '',
  credits: ''
})
const errorMessage = ref('')
const expandedRows = ref([])  // Track expanded rows
const courseStudents = ref({})  // Store students for each course
const showTooltip = ref({})  // Track tooltip visibility
const page = ref(1)
const limit = 10
const total = ref(0)

const filteredCourses = computed(() => {
  if (!searchKeyword.value.trim()) {
    return courses.value
  }
  const keyword = searchKeyword.value.toLowerCase().trim()
  return courses.value.filter(course => {
    return (
      (course.course_code && course.course_code.toLowerCase().includes(keyword)) ||
      (course.course_name && course.course_name.toLowerCase().includes(keyword)) ||
      (course.teacher && course.teacher.toLowerCase().includes(keyword)) ||
      (course.credits && String(course.credits).includes(keyword))
    )
  })
})

const fetchCourses = async () => {
  try {
    const response = await axios.get('/api/courses', {
      params: { page: page.value, limit }
    })
    courses.value = response.data.data || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching courses:', error)
    courses.value = []
    total.value = 0
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchCourses()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

const resetForm = () => {
  currentCourse.value = {
    course_code: '',
    course_name: '',
    teacher: '',
    credits: ''
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  // 如果是只读模式，不允许提交
  if (props.readonly) {
    alert('学生无权添加或修改课程信息')
    showForm.value = false
    resetForm()
    return
  }
  
  try {
    if (isEdit.value) {
      await axios.put(`/api/courses/${currentCourse.value.id}`, currentCourse.value)
    } else {
      await axios.post('/api/courses', currentCourse.value)
    }
    showForm.value = false
    resetForm()
    await fetchCourses()
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '操作失败'
  }
}

const editCourse = (course) => {
  if (props.readonly) {
    alert('学生无权编辑课程信息')
    return
  }
  currentCourse.value = { ...course }
  isEdit.value = true
  showForm.value = true
}

const deleteCourse = async (course_id) => {
  if (props.readonly) {
    alert('学生无权删除课程信息')
    return
  }
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/courses/${course_id}`)
      // 如果删除后当前页没有数据，返回上一页
      if (courses.value.length === 1 && page.value > 1) {
        page.value--
      }
      await fetchCourses()
    } catch (error) {
      console.error('Error deleting course:', error)
    }
  }
}

const toggleExpand = async (courseId) => {
  const index = expandedRows.value.indexOf(courseId)
  if (index === -1) {
    expandedRows.value.push(courseId)
    if (!courseStudents.value[courseId]) {
      await fetchCourseStudents(courseId)
    }
  } else {
    expandedRows.value.splice(index, 1)
  }
}

const fetchCourseStudents = async (courseId) => {
  try {
    const response = await axios.get('/api/student-courses', {
      params: { course_id: courseId }
    })
    console.log('Fetched course students for course', courseId, ':', response.data)
    
    // Get unique students (in case there are multiple records for same student)
    const studentsMap = {}
    response.data.forEach(sc => {
      if (sc.course_id == courseId && sc.student_id) {
        const key = sc.student_id
        if (!studentsMap[key]) {
          studentsMap[key] = {
            student_id: sc.student_id,
            student_name: sc.student_name || '未知',
            exam_score: sc.exam_score ?? 0,
            daily_score: sc.daily_score ?? 0,
            final_score: sc.final_score ?? 0,
            semester: sc.semester || ''
          }
        }
      }
    })
    courseStudents.value[courseId] = Object.values(studentsMap)
    console.log('Processed students for course', courseId, ':', courseStudents.value[courseId])
  } catch (error) {
    console.error('Error fetching course students:', error)
    courseStudents.value[courseId] = []
  }
}

const showButtonTooltip = (courseId) => {
  if (!expandedRows.value.includes(courseId)) {
    showTooltip.value[courseId] = true
  }
}

const hideButtonTooltip = (courseId) => {
  showTooltip.value[courseId] = false
}

// 获取指定课程的学生数量
const getStudentCount = (courseId) => {
  const students = courseStudents.value[courseId]
  return students ? students.length : 0
}

onMounted(() => {
  fetchCourses()
  console.log('CourseManagement readonly prop:', props.readonly)
})
</script>

<template>
  <div>
    <!-- 只读模式：学生只能查看 -->
    <template v-if="readonly">
      <div class="readonly-header">
        <h3 class="section-title-blue">📚 所有课程</h3>
        <div class="search-container">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="🔍 搜索课程（课程代码、名称、教师、学分）" 
            class="search-input"
          />
          <span v-if="searchKeyword" class="search-result">
            找到 {{ filteredCourses.length }} 条记录
          </span>
        </div>
      </div>
    </template>
    <!-- 管理员模式：可以添加和编辑 -->
    <template v-else>
      <div class="toolbar">
        <button @click="showForm = true; resetForm()" class="add-button-blue">
          <span style="margin-right: 6px;">➕</span>添加课程
        </button>
        <div class="search-container">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="🔍 搜索课程（课程代码、名称、教师、学分）" 
            class="search-input"
          />
          <span v-if="searchKeyword" class="search-result">
            找到 {{ filteredCourses.length }} 条记录
          </span>
        </div>
      </div>
    </template>
    
    <table v-if="filteredCourses.length">
        <thead>
          <tr>
            <th></th>  <!-- Expand column -->
            <th>课程代码</th>
            <th>课程名称</th>
            <th>教师</th>
            <th>学分</th>
            <th v-if="!readonly">操作</th>
          </tr>
        </thead>
      <tbody>
        <template v-for="course in filteredCourses" :key="course.id">
          <tr>
            <td>
              <div 
                class="expand-button-container"
                @mouseenter="showButtonTooltip(course.id)"
                @mouseleave="hideButtonTooltip(course.id)"
              >
                <button 
                  @click.stop="toggleExpand(course.id)"
                  class="expand-button"
                >{{ expandedRows.includes(course.id) ? '-' : '+' }}</button>
                <div v-if="!expandedRows.includes(course.id) && showTooltip[course.id]" class="custom-tooltip">
                  选择该课程的学生
                </div>
              </div>
            </td>
            <td>{{ course.course_code }}</td>
            <td>{{ course.course_name }}</td>
            <td>{{ course.teacher }}</td>
            <td>{{ course.credits }}</td>
            <td v-if="!readonly">
              <button @click.stop="editCourse(course)">编辑</button>
              <button @click.stop="deleteCourse(course.id)">删除</button>
            </td>
          </tr>
          <tr v-if="expandedRows.includes(course.id)" class="expanded-row">
            <td :colspan="readonly ? 5 : 6" class="expanded-cell">
              <div class="expanded-content">
                <!-- 只读模式：只显示学生数量 -->
                <template v-if="readonly">
                  <h4 class="section-title-blue">👥 选择该课程的学生</h4>
                  <p class="student-count">
                    <strong>选课人数：{{ getStudentCount(course.id) }}</strong>
                  </p>
                  <p v-if="getStudentCount(course.id) === 0" class="empty-state">
                    暂无学生选择此课程
                  </p>
                </template>
                <!-- 管理员模式：显示详细信息表格 -->
                <template v-else>
                  <h4 class="section-title-blue">👥 选择该课程的学生</h4>
                  <table class="sub-table">
                    <thead>
                      <tr>
                        <th>学生姓名</th>
                        <th>学号</th>
                        <th>考试成绩</th>
                        <th>平时成绩</th>
                        <th>总成绩</th>
                        <th>学期</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="student in courseStudents[course.id]" :key="student.student_id">
                        <td>{{ student.student_name }}</td>
                        <td>{{ student.student_id }}</td>
                        <td>{{ student.exam_score ?? 0 }}</td>
                        <td>{{ student.daily_score ?? 0 }}</td>
                        <td>{{ student.final_score ?? 0 }}</td>
                        <td>{{ student.semester || '' }}</td>
                      </tr>
                      <tr v-if="!courseStudents[course.id] || courseStudents[course.id].length === 0">
                        <td colspan="6" class="empty-state">暂无学生选择此课程</td>
                      </tr>
                    </tbody>
                  </table>
                </template>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <p v-else-if="!searchKeyword">暂无课程</p>
    <p v-else>未找到匹配的课程</p>

    <div v-if="total > 0 && !searchKeyword" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <div v-if="showForm && !readonly" class="modal">
      <div class="modal-content">
        <h2>{{ isEdit ? '编辑课程' : '添加课程' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group">
            <input v-model="currentCourse.course_code" placeholder="课程代码" required :disabled="isEdit" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">课程代码: 不可重复</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentCourse.course_name" placeholder="课程名称" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">课程名称: 课程的全称</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentCourse.teacher" placeholder="教师" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">教师: 授课老师姓名</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentCourse.credits" type="number" placeholder="学分" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学分: 1到10</div>
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
/* 蓝色主题 - 课程管理 */
:root {
  --theme-primary: #2196f3;
  --theme-primary-dark: #1976d2;
  --theme-primary-light: #e3f2fd;
  --theme-hover: #f3f8ff;
}

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
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
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
  background-color: #f3f8ff;
  transform: scale(1.001);
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.1);
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
.toolbar, .readonly-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.readonly-header {
  flex-direction: column;
  align-items: flex-start;
}

.add-button-blue {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  white-space: nowrap;
}

.add-button-blue:hover {
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
}

.search-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
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
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.search-result {
  color: #2196f3;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.section-title-blue {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 22px;
  font-weight: 600;
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 展开行 */
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

.section-title-blue {
  color: #2196f3;
  font-weight: 600;
  margin: 0 0 15px 0;
  font-size: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.student-count {
  margin: 0;
  color: #333;
  font-size: 16px;
  padding: 12px;
  background: #e3f2fd;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 20px;
  font-style: italic;
}

/* 子表格 */
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
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  padding: 12px;
  font-size: 13px;
}

.sub-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.sub-table tbody tr:hover {
  background-color: #e3f2fd;
}

/* 展开按钮 */
.expand-button-container {
  position: relative;
  display: inline-block;
}

.expand-button {
  cursor: pointer;
  padding: 6px 12px;
  min-width: 32px;
  height: 32px;
  border: 2px solid #2196f3;
  background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-weight: 600;
  color: #2196f3;
  font-size: 16px;
}

.expand-button:hover {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);
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
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
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
  border-color: #2196f3;
  background: white;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.info-container {
  position: relative;
  margin-left: 10px;
}

.info-ellipsis {
  cursor: pointer;
  color: #2196f3;
  font-weight: bold;
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e3f2fd;
  transition: all 0.3s ease;
}

.info-ellipsis:hover {
  background: #2196f3;
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
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
}

button[type="submit"]:hover {
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
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

p[style*="color: #999"] {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #2196f3;
  font-weight: 500;
}
</style>

