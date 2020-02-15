# coding=utf-8
import time
import pandas as pd
import numpy as np
from scipy.optimize import linprog

class project_analyze:
    def __init__(self,staffFile,projectFile,gamma = -0.3 ):
        self.staffDf = pd.read_csv(staffFile,encoding = 'utf8',header = 0,engine ='c')
        self.projectDf = pd.read_csv(projectFile,encoding = 'utf8',engine ='c')
        
        self.projectNum = self.projectDf.shape[0]
        self.staffNum = self.staffDf.shape[0]
        self.c = []        #优化目标: [c[项目i][员工j] , c[项目i][员工j+1], ..... ,c[项目i+1][员工j] , c[项目i+1][员工j+1]]
        self.bounds = []   #边界:     [(项目i中员工j的最低贡献度,项目i中员工j的最高贡献度),(项目i中员工j+1的最低贡献度,项目i中员工j+1的最高贡献度)..]
        self.A_ub = []
        self.B_ub = []
        self.A_eq = []
        self.B_eq = []
        self.__cal_lingo_c()
        self.__cal_lingo_bounds()
        self.__cal_lingo_A_ub()
        self.__cal_lingo_B_ub(gamma)
        
        print("项目数量:",self.projectNum)
        print("人员数量:",self.staffNum)
        print("Creat project analyze.")
    
    def __cal_lingo_c(self):
        ability = list(self.projectDf.columns)
        ability = ability[2:-2]
        for proNum in range(self.projectNum):
            projectVec = np.array(self.projectDf.loc[proNum,ability])
            for staNum in range(self.staffNum):
                staffVec = np.array(self.staffDf.loc[staNum,ability])
                abiValue = np.sum(staffVec*projectVec)
                if(self.projectDf.loc[proNum,"人员加成"]) == self.staffDf.loc[staNum,"姓名"]:
                    abiValue += 0.15
                self.c.append(-abiValue)
 
                
    def __cal_lingo_bounds(self):
        for i in range(self.projectNum):
            for j in range(self.staffNum):
                self.bounds.append((0,1))
        
    def __cal_lingo_A_ub(self):
        for i in range(self.staffNum):
            vector = (i*[0]+[1]+(self.staffNum-i-1)*[0])*self.projectNum
            self.A_ub.append(vector)
        for i in range(self.projectNum):
            vector = (i*self.staffNum*[0]+self.staffNum*[-1]+self.staffNum*(self.projectNum-i-1)*[0])
            self.A_ub.append(vector)

  
    def __cal_lingo_B_ub(self,gamma):  
        workLoad = np.array(self.projectDf["紧急程度"])*gamma
        self.B_ub = [1]*self.staffNum + list(workLoad)
        

    def get_lingo_paramter(self):
        return [self.c,self.A_ub,self.B_ub,self.bounds]
    
     
    
    def __get_value(self,a):
        return a[1]
    
    def staff_recommend(self,projectName):
        ability = list(self.projectDf.columns)
        ability = ability[2:-2]   
        recommendList = []
        projectVec = np.array(self.projectDf.loc[self.projectDf["项目名称"]==projectName,ability])
        for staNum in range(self.staffNum):
            staffVec = np.array(self.staffDf.loc[staNum,ability])
            abiValue = np.sum(staffVec*projectVec)
            
            if self.projectDf.loc[self.projectDf["项目名称"]==projectName,"人员加成"].iloc[0] == self.staffDf.loc[staNum,"姓名"]:
                abiValue += 0.15
            recommendList.append((self.staffDf.loc[staNum,"姓名"],abiValue))
            recommendList.sort(key=self.__get_value,reverse = True)
        return recommendList
    
    def team_evaluate(self,teamStaff,projectName):
        ability = list(self.projectDf.columns)
        ability = ability[2:-2]          
        teamSize = len(teamStaff)
        abiValue = 0
        projectVec = np.array(self.projectDf.loc[self.projectDf["项目名称"]==projectName,ability])
        for staffName in teamStaff:
            staffVec = np.array(self.staffDf.loc[self.staffDf["姓名"]==staffName,ability])
            abiValue += np.sum(staffVec*projectVec)
            if self.projectDf.loc[self.projectDf["项目名称"]==projectName,"人员加成"].iloc[0] == staffName:
                abiValue += 0.15

        abiValueMax = 0  
        teamMax = self.staff_recommend(projectName)[0:5]
        for staffName in teamMax:
            staffVec = np.array(self.staffDf.loc[self.staffDf["姓名"]==staffName[0],ability])
            abiValueMax += np.sum(staffVec*projectVec)
            if self.projectDf.loc[self.projectDf["项目名称"]==projectName,"人员加成"].iloc[0] == staffName[0]:
                abiValueMax += 0.15        
        
        print("输入团队{}在项目{}中的评分为{:.3f}".format(teamStaff,projectName,abiValue))
        print("最优团队{}在项目{}中的评分为{:.3f}".format([i[0] for i in teamMax],projectName,abiValueMax))
    
    def optimize_lingo(self):
        self.ans = linprog(c=self.c , A_ub = self.A_ub , b_ub = self.B_ub , bounds = self.bounds)
        self.analyzeVec = self.ans["x"]
        #print(self.analyzeVec)
        
    def consequence(self):   
        try:
            consDf = pd.DataFrame(index=list(self.projectDf["项目名称"]),columns=list(self.staffDf["姓名"]))
            for i in range(self.projectNum):
              project_plan = self.analyzeVec[i*self.staffNum:i*self.staffNum+self.staffNum]
              #print("项目",self.projectDf.loc[i,"项目名称"],"人员投入计划")
              for j in range(len(project_plan)):
                  if project_plan[j] >= 0.01:
                      consDf.iloc[i,j] = project_plan[j]
            consDf.fillna(0,inplace=True)
            consDf.to_csv("项目人员分配计划.csv")                                                                                                                                            
                        
        except:
            print("You need run method \"optimize_lingo\"")
    
    def show_lingo(self):
        print("message:",self.ans["message"])
        print("fun:",-self.ans["fun"])
        print("nit:",self.ans["nit"])

if __name__ == "__main__":
   analyze = project_analyze("staff_info.csv", "project_info.csv")
   lingoParamter = analyze.get_lingo_paramter()
   c = lingoParamter[0]
   A_ub = lingoParamter[1]
   B_ub = lingoParamter[2]
   bounds = lingoParamter[3]
   
   #print(c)
   #print(A_ub)
   #print(B_ub)
   #print("c:",len(c))
   #print("A_ub:",len(A_ub),len(A_ub[0]))
   #print("B_ub:",len(B_ub))
   #print("bou_ub:",len(bounds),len(bounds[0]))
   
   
   #start = time.time()   
   #analyze.optimize_lingo()
   #cost = time.time() - start  
   #print("耗时{:.2f}s.".format(cost))   
   #analyze.consequence()
   #analyze.show_lingo()
   
   print(analyze.staff_recommend("F"))
   analyze.team_evaluate(["A1","A3","A5","A7","A9"], "F")
